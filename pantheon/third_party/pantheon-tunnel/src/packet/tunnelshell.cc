/* -*-mode:c++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */

#include <deque>
#include <thread>
#include <chrono>

#include <sys/socket.h>
#include <net/route.h>

#include "tunnelshell.hh"
#include "netdevice.hh"
#include "system_runner.hh"
#include "util.hh"
#include "interfaces.hh"
#include "address.hh"
#include "timestamp.hh"
#include "exception.hh"
#include "config.h"

#define UDP_PACKET_HEADER_SIZE 28

using namespace std;
using namespace PollerShortNames;

uint64_t CalcAdditionalDelay(float delay_ts_prev,
                             float delay_prev,
                             float delay_ts_next,
                             float delay_next,
                             uint64_t tc) {
    // TODO: can add smoothing based on delay timestamp
    return static_cast<uint64_t>(delay_next);
}

TunnelShell::TunnelShell( void )
    : outside_shell_loop()
{
    /* make sure environment has been cleared */
    if ( environ != nullptr ) {
        throw runtime_error( "TunnelShell: environment was not cleared" );
    }
}

void TunnelShell::start_link( char ** const user_environment, UDPSocket & peer_socket,
                  const Address & local_private_address,
                  const Address & peer_private_address,
                  std::unique_ptr<std::ofstream> &ingress_log,
                  std::unique_ptr<std::ofstream> &egress_log,
                  const string & shell_prefix,
                  const vector< string > & command,
                  const std::string &latency_log_name)
{
    /* Fork */
    outside_shell_loop.add_child_process( "packetshell", [&]() { // XXX add special child process?
            TunDevice tun( "tunnel", local_private_address, peer_private_address, false );
            deque<uint64_t> timestamp_list;
            deque<string> packet_list;
            float delay_ts_prev = 0, delay_ts_next = 0;
            float delay_prev = 0, delay_next = 0;

            std::unique_ptr<std::ifstream> latency_log;
            if (!latency_log_name.empty()) {
                latency_log.reset( new std::ifstream( latency_log_name ) );
                if ( not latency_log->good() ) {
                    throw runtime_error( "Error Open Latency Log" );
                }
            }

            interface_ioctl( SIOCSIFMTU, "tunnel",
                             [] ( ifreq &ifr ) { ifr.ifr_mtu = 1500 - UDP_PACKET_HEADER_SIZE - sizeof( wrapped_packet_header ); } );

            /* bring up localhost */
            interface_ioctl( SIOCSIFFLAGS, "lo",
                             [] ( ifreq &ifr ) { ifr.ifr_flags = IFF_UP; } );

            /* create default route */
            rtentry route;
            zero( route );

            route.rt_gateway = peer_private_address.to_sockaddr();
            route.rt_dst = route.rt_genmask = Address().to_sockaddr();
            route.rt_flags = RTF_UP | RTF_GATEWAY;

            SystemCall( "ioctl SIOCADDRT", ioctl( UDPSocket().fd_num(), SIOCADDRT, &route ) );

            EventLoop inner_loop;

            /* Fork again after dropping root privileges */
            drop_privileges();

            /* restore environment */
            environ = user_environment;

            /* set MAHIMAHI_BASE if not set already to indicate outermost container */
            SystemCall( "setenv", setenv( "MAHIMAHI_BASE",
                                          peer_private_address.ip().c_str(),
                                          false /* don't override */ ) );

            inner_loop.add_child_process( join( command ), [&]() {
                    /* tweak bash prompt */
                    prepend_shell_prefix( shell_prefix );

                    return ezexec( command, true );
                } );

            /* tun device gets datagram -> read it -> give to server socket */
            inner_loop.add_simple_input_handler( tun,
                    [&] () {
                    const string packet = tun.read();

                    const struct wrapped_packet_header to_send = { uid_++ };

                    string uid_wrapped_packet = string( (char *) &to_send, sizeof(struct wrapped_packet_header) ) + packet;

                    uint64_t ts = timestamp_usecs();
                    if ( egress_log ) {
                        *egress_log << pretty_microseconds( ts ) << " - " << to_send.uid << " - " << uid_wrapped_packet.length() + UDP_PACKET_HEADER_SIZE << endl;
                    }

                    packet_list.push_back(uid_wrapped_packet);
                    if (latency_log && latency_log->good()) {
                        while (delay_ts_next < ts) {
                            delay_ts_prev = delay_ts_next;
                            delay_prev = delay_next;

                            *latency_log >> delay_ts_next;
                            *latency_log >> delay_next;
                            if ( not latency_log->good() ) {
                                /*latency_log.reset( new std::ifstream( latency_log_name ) );
                                *latency_log >> delay_ts;
                                *latency_log >> delay;*/

                                delay_ts_next = delay_ts_prev;
                                delay_next = delay_prev;
                                cerr << "Reach Delay Trace End: additional delay stays " << delay_next << endl;
                                break;
                            }
                        }
                        timestamp_list.push_back(ts + CalcAdditionalDelay(delay_ts_prev, delay_prev, delay_ts_next, delay_next, ts));
                    } else {
                        timestamp_list.push_back(ts + static_cast<uint64_t>(delay_next));
                    }

                    return ResultType::Continue;
                    } );

            inner_loop.add_self_input_handler( peer_socket,
                    [&] () {
                    while (!packet_list.empty()) {
                        if (timestamp_list.front() > timestamp_usecs()) {
                            break;
                        }
                        peer_socket.write( packet_list.front() );
                        packet_list.pop_front();
                        timestamp_list.pop_front();
                    }

                    return ResultType::Continue;
                    } );

            /* we get datagram from peer_socket process -> write it to tun device */
            inner_loop.add_simple_input_handler( peer_socket,
                    [&] () {
                    const string packet = peer_socket.read();

                    const struct wrapped_packet_header header_received = *( (struct wrapped_packet_header *) packet.data() );

                    string contents = packet.substr( sizeof(struct wrapped_packet_header) );
                    if ( contents.empty() ) {
                        if ( header_received.uid == (uint64_t) -1 ) {
                            cerr << "Got extra tunnelclient syn packet, responding again.." << endl;

                            send_wrapper_only_datagram(peer_socket, (uint64_t) -2 );
                            return ResultType::Continue;
                        } else if ( header_received.uid == (uint64_t) -2 ) {
                            // Got extra ack from server, ignore
                            return ResultType::Continue;
                        } else {
                            cerr << "packet empty besides uid " << header_received.uid << endl;
                            return ResultType::Exit;
                        }
                    }

                    if ( ingress_log ) {
                        *ingress_log << pretty_microseconds( timestamp_usecs() ) << " - " << header_received.uid << " - " << packet.length() + UDP_PACKET_HEADER_SIZE << endl;
                    }

                    tun.write( contents );
                    return ResultType::Continue;
                    } );

            /* exit if finished
            inner_loop.add_action( Poller::Action( peer_socket, Direction::Out,
                        [&] () {
                        return ResultType::Exit;
                        } ); */

            return inner_loop.loop();
        }, true );  /* new network namespace */
}

int TunnelShell::wait_for_exit( void ) {
    return outside_shell_loop.loop();
}
