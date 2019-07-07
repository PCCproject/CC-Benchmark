var json_data = undefined;

$.getJSON('res2.json', function(data) {
  json_data = data;
});

function get_rgb(normalized_val) {
  var green = 0;
  if (normalized_val >= 0.5) {
    green = 255;
  } else {
    green = 255 * (normalized_val / 0.5);
  }

  var red = 0;
  if (normalized_val <= 0.5) {
    red = 255;
  } else {
    red = 255 * (1 - normalized_val) / 0.5;
  }

  return 'background-color: rgb(' + red + ',' + green + ',0)'
}
function table_formatter(type) {
  var return_str = "";
  for (var i = 0; i < json_data.Tests.length; i++) {
    return_str += "<tr>";
    var curr_test = json_data.Tests[i];
    console.log(curr_test);
    var test_name = curr_test.name;
    var metrics = curr_test[type];
    var copa = metrics.copa;
    var vivace = metrics.vivace;
    var cubic = metrics.cubic;
    var pcc = metrics.pcc;
    var bbr = metrics.bbr;
    var taova = metrics.taova;
    var vegas = metrics.vegas;
    var sprout = metrics.sprout;
    var ledbat = metrics.ledbat;

    var copa_bg = get_rgb(copa);
    var vivace_bg = get_rgb(vivace);
    var cubic_bg = get_rgb(cubic);
    var pcc_bg = get_rgb(pcc);
    var bbr_bg = get_rgb(bbr);
    var taova_bg = get_rgb(taova);
    var vegas_bg = get_rgb(vegas);
    var sprout_bg = get_rgb(sprout);
    var ledbat_bg = get_rgb(ledbat);
    console.log(copa_bg)
    console.log(copa)
    //background-color: rgb(201, 76, 76);

    return_str += ("<th class='description'>" + test_name + "</th>");
    return_str += ("<th class='cell' style='" + copa_bg + "'>" + copa + "</th>");
    return_str += ("<th class='cell' style='" + vivace_bg + "'>" + vivace + "</th>");
    return_str += ("<th class='cell' style='" + cubic_bg + "'>" + cubic + "</th>");
    return_str += ("<th class='cell' style='" + pcc_bg + "'>" + pcc + "</th>");
    return_str += ("<th class='cell' style='" + bbr_bg + "'>" + bbr + "</th>");
    return_str += ("<th class='cell' style='" + taova_bg + "'>" + taova + "</th>");
    return_str += ("<th class='cell' style='" + vegas_bg + "'>" + vegas + "</th>");
    return_str += ("<th class='cell' style='" + sprout_bg + "'>" + sprout + "</th>");
    return_str += ("<th class='cell' style='" + ledbat_bg + "'>" + ledbat + "</th>");
    return_str += "</tr>";
  }

  return return_str;
}

function disp_power_metric() {
  console.log(json_data);
  var s = table_formatter('overall');
  document.getElementById("table-body").innerHTML = s;
}

function disp_latency() {
  console.log(json_data);
  var s = table_formatter('lat');
  document.getElementById("table-body").innerHTML = s;
}

function disp_thpt() {
  console.log(json_data);
  var s = table_formatter('thpt');
  document.getElementById("table-body").innerHTML = s;
}

function disp_loss() {
  console.log(json_data);
  var s = table_formatter('loss');
  document.getElementById("table-body").innerHTML = s;
}
