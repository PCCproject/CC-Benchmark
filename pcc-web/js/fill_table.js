var json_data = undefined;

$.getJSON('../test_data/public_scheme_metrics.json', function(data) {
  json_data = data;
});

function get_rgb(normalized_val) {
  if (normalized_val === "N/A" || normalized_val == undefined) {
    return 'background-color: rgb(255, 255, 255)'
  }
  if (normalized_val > 1) {
    normalized_val = 1;
  }

  if (normalized_val < 0) {
    normalized_val = 0;
  }

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

function upperCaseFirst(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

function round(num) {
    return Math.ceil(num * 100) / 100;
}

function getDisplayName(curr_test) {
  if (curr_test.alias != undefined) {
    return curr_test.alias;
  }

  var test_name = curr_test.name;
  var ret = "";
  var split_name = test_name.split('_');
  for (var i = 0; i < split_name.length - 1; i++) {
    ret += upperCaseFirst(split_name[i]);
    ret += ' ';
  }

  return ret;
}

function table_formatter(type) {
  var return_str = "";
  for (var i = 0; i < json_data.Tests.length; i++) {
    return_str += "<tr>";
    var curr_test = json_data.Tests[i];
    var test_name = curr_test.name;
    var metrics = curr_test[type];

    var copa = (metrics.copa == undefined) ? "N/A" : round(metrics.copa);
    var vivace = (metrics.vivace_latency == undefined) ? "N/A" : round(metrics.vivace_latency);
    var cubic = (metrics.default_tcp == undefined) ? "N/A" : round(metrics.default_tcp);
    var bbr = (metrics.bbr == undefined) ? "N/A" : round(metrics.bbr);
    var taova = (metrics.taova == undefined) ? "N/A" : round(metrics.taova);
    var vegas = (metrics.vegas == undefined) ? "N/A" : round(metrics.vegas);
    var sprout = (metrics.sprout == undefined) ? "N/A" : round(metrics.sprout);
    var ledbat = (metrics.ledbat == undefined) ? "N/A" : round(metrics.ledbat);

    var copa_bg = get_rgb(metrics["copa score"]);
    var vivace_bg = get_rgb(metrics["vivace_latency score"]);
    var cubic_bg = get_rgb(metrics["default_tcp score"]);
    var bbr_bg = get_rgb(metrics["bbr score"]);
    var taova_bg = get_rgb(metrics["taova score"]);
    var vegas_bg = get_rgb(metrics["vegas score"]);
    var sprout_bg = get_rgb(metrics["sprout score"]);
    var ledbat_bg = get_rgb(metrics["ledbat score"]);
    // console.log(vivace_bg)
    // console.log(vivace)
    //background-color: rgb(201, 76, 76);
    var displayName = getDisplayName(curr_test);

    return_str += ("<th class='description'><a href=test_data/" + test_name + "/index.html>" + displayName + "</a></th>");
    return_str += ("<th class='cell' style='" + copa_bg + "'>" + copa + "</th>");
    return_str += ("<th class='cell' style='" + vivace_bg + "'>" + vivace + "</th>");
    return_str += ("<th class='cell' style='" + cubic_bg + "'>" + cubic + "</th>");
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
  // console.log(json_data);
  var s = table_formatter('overall');
  document.getElementById("table-body").innerHTML = s;
  document.getElementById("metric-description").innerHTML = '<pre>Number: log(mean throughput / 95% delay) (Kleinrock\'s power metric)' +
  '<br>Color: log(mean throughput / 95% delay) / 7';
}

function disp_latency() {
  // console.log(json_data);
  var s = table_formatter('95 qdelay');
  document.getElementById("table-body").innerHTML = s;
  document.getElementById("metric-description").innerHTML = '<pre>Number: 95% queueing delay among all tests, in ms' +
  '<br>Color: 1 - (95% delay / 60ms)';
}

function disp_thpt() {
  // console.log(json_data);
  var s = table_formatter('avg thrput');
  document.getElementById("table-body").innerHTML = s;
  document.getElementById("metric-description").innerHTML = '<pre>Number: Mean throughput among all tests, in Mbps' +
  '<br>Color: Mean throughput / link bottleneck';
}

function disp_loss() {
  // console.log(json_data);
  var s = table_formatter('avg loss');
  document.getElementById("table-body").innerHTML = s;
  document.getElementById("metric-description").innerHTML = '<pre>Number: Mean fraction of packets lost' +
  '<br>Color: 1 - 10*( (measured loss - random loss) / (1 - random loss) )';
}

function saveData(key,value) {
  localStorage.setItem(key,value) || (document.cookie = key + "=" + value);
}

function getData(key) {
  return localStorage.getItem(key) || document.cookie.match(new RegExp(key + "\=(.+?)(?=;)"))[1];
}
