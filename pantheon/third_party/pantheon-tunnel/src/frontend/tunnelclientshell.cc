/* -*-mode:c++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */

#include <vector>
#include <string>
#include <iostream>
#include <fstream>
#include <memory>
#include <getopt.h>

#include "exception.hh"
#include "tunnelshell_common.hh"
#include "tunnelshell.hh"
#include "timestamp.hh"

using namespace std;
using namespace PollerShortNames;

void usage_error( const string & program_name )
{
    cerr << "Usage: " << program_name << " IP PORT LOCAL-PRIVATE-IP SERVER-PRIVATE-IP [OPTION]... [COMMAND]" << endl;
    cerr << endl;
    cerr << "Options = --ingress-log=FILENAME --egress-log=FILENAME --latency-log=FILENAME --interface=INTERFACE" << endl;

    throw runtime_error( "invalid arguments" );
}

int main( int argc, char *argv[] )
{
    try {
        /* clear environment while running as root */
        char ** const user_environment = environ;
        environ = nullptr;

        check_requirements( argc, argv );

        if ( argc < 5 ) {
            usage_error( argv[ 0 ] );
        }

        const option command_line_options[] = {
            { "ingress-log", required_argument, nullptr, 'n' },
            { "egress-log",  required_argument, nullptr, 'e' },
            { "latency-log", required_argument, nullptr, 'l' },
            { "interface",   required_argument, nullptr, 'i' },
            { 0,                             0, nullptr,  0  }
        };

        string ingress_log_name, egress_log_name, latency_log_name, if_name;

        while ( true ) {
            const int opt = getopt_long( argc, argv, "",
                                         command_line_options, nullptr );
            if ( opt == -1 ) { /* end of options */
                break;
            }

            switch ( opt ) {
            case 'n':
                ingress_log_name = optarg;
                break;
            case 'e':
                egress_log_name = optarg;
                break;
            case 'l':
                latency_log_name = optarg;
                break;
            case 'i':
                if_name = optarg;
                break;
            case '?':
                usage_error( argv[ 0 ] );
                break;
            default:
                throw runtime_error( "getopt_long: unexpected return value " +
                                     to_string( opt ) );
            }
        }

        if ( optind + 4 > argc ) {
            usage_error( argv[ 0 ] );
        }

        const Address server{ argv[ optind ], argv[ optind + 1 ] };
        const Address local_private_address { argv[ optind + 2 ], "0" };
        const Address server_private_address { argv[ optind + 3 ], "0" };

        vector< string > command;

        if ( optind + 4 == argc ) {
            command.push_back( shell_path() );
        } else {
            for ( int i = optind + 4; i < argc; i++ ) {
                command.push_back( argv[ i ] );
            }
        }

        UDPSocket server_socket;

        if ( !if_name.empty() ) {
            /* bind the server socket to a specified interface */
            check_interface_for_binding( string( argv[ 0 ] ), if_name );
            server_socket.bind( if_name );
        }

        /* connect the server_socket to the server_address */
        server_socket.connect( server );
        cerr << "Tunnelclient listening for server on port " << server_socket.local_address().port() << endl;
        // XXX error better if this write fails because server is not accepting connections

        std::unique_ptr<std::ofstream> ingress_log, egress_log;
        initialize_logfile( ingress_log, ingress_log_name, argc, argv, "ingress" );
        initialize_logfile( egress_log, egress_log_name, argc, argv, "egress" );

        bool got_ack = false;
        const int retry_loops = 40;
        int retry_num = 0;
        while (not got_ack) {
            try {
                send_wrapper_only_datagram( server_socket, (uint64_t) -1 );
            } catch ( const exception & e ) {
                cerr << "Tunnelclient ignoring exception sending a syn: ";
                print_exception( e );
            }

            Poller ack_poll;
            ack_poll.add_action( Poller::Action( server_socket, Direction::In,
                        [&] () {
                        const string ack_packet = server_socket.read();
                        const wrapped_packet_header ack_header = *( (wrapped_packet_header *) ack_packet.data() );
                        if (ack_packet.length() == sizeof(wrapped_packet_header) && ack_header.uid == (uint64_t) -2) {
                            got_ack = true;
                        }
                        return ResultType::Exit;
                        } ) );
            ack_poll.poll( 500 );

            if (not got_ack) {
                retry_num++;
                if (retry_num > retry_loops) {
                    cerr << "Failed to connect to tunnel server after " << retry_loops << " tries, exiting.." << endl;
                    return EXIT_FAILURE;
                } else {
                    cerr << "Tunnelclient received no response from tunnelserver, retrying " << retry_num << "/" << retry_loops << endl;
                }
            }
        }
        cout << "Tunnelclient got connection from tunnelserver at " << server_socket.peer_address().ip() << endl;

        TunnelShell tunnelclient;
        tunnelclient.start_link( user_environment, server_socket,
                                 local_private_address, server_private_address,
                                 ingress_log, egress_log,
                                 "[tunnelclient " + server.str() + "] ",
                                 command,
                                 latency_log_name );
        return tunnelclient.wait_for_exit();
    } catch ( const exception & e ) {
        cerr << "Tunnelclient got an exception. ";
        print_exception( e );
        return EXIT_FAILURE;
    }
}
