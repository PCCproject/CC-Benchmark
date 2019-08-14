var json_data = undefined;
var indev_data = undefined;
var listOfIndevScheme = new Set();
var publicTestSchemes = ['copa', 'vivace_latency', 'default_tcp', 'bbr', 'vegas', 'ledbat'];
var benchmarkSchemes = ['copa', 'vivace_latency', 'bbr'];
var g_indev_branches = [];

$.getJSON('../test_data/public_scheme_metrics.json', function(data) {
  json_data = data;
});

function getBranchName(scheme_name) {
   var scheme_parts = scheme_name.split(',');
   return scheme_parts[0] + "," + scheme_parts[1]; 
}

$.getJSON('../test_data/indev_scheme_metrics.json', function(data) {
  indev_data = data;
  for (var i = 0; i < indev_data.Tests.length; i++) {
    var curr_test = indev_data.Tests[i].overall;
    Object.keys(curr_test).forEach(item => {
      var branch_name = getBranchName(item);
      if (g_indev_branches.includes(branch_name) == false) {
          g_indev_branches.push(branch_name);
      }
      var c = item[item.length - 6];
      if (c != ' ') {
        listOfIndevScheme.add(item);
      }
    });
  }
});

function getIndevSchemeHeader(branch_name) {
    var result = "<thead><tr>";
    result += "<th class='description' style='text-decoration: none;'>Test Scenario</th>";
    var html_bracket = '<th class="cell" style="white-space:pre">';
    var html_bracket_end = '</th>';

    benchmarkSchemes.forEach(item => {
        result += html_bracket;
        result += item;
        result += html_bracket_end;
    });

    listOfIndevScheme.forEach(item => {
        if (getBranchName(item) == branch_name) {
            result += html_bracket;
            var split = item.split(',');
            result += split[0];
            result += ':<br>';
            result += split[1];
            result += ':<br>';
            result += split[2];
            result += html_bracket_end;
        }
    });
    
    result += "</tr></thead>";
    return result;
}

function getIndevTableBody(branch_name, type) {
  var return_str = "<tbody>";
  for (var i = 0; i < indev_data.Tests.length; i++) {
    return_str += "<tr>";
    var curr_test = indev_data.Tests[i];
    var test_name = curr_test.name;
    var benchmarkTest = getBenchmarkTest(test_name);
    var benchmarkMetrics = benchmarkTest[type];
    var metrics = curr_test[type];
    var displayName = getDisplayName(curr_test);
    return_str += ("<th class='description'><a href=../test_data/" + test_name + "/indev_index.html>" + displayName + "</a></th>");

    benchmarkSchemes.forEach(item => {
        var displayNumber = (benchmarkMetrics[item] == undefined ? 'N/A' : round(benchmarkMetrics[item]));
        var displayRGB = get_rgb(benchmarkMetrics[item + ' score']);
        return_str += ("<th class='cell' style='" + displayRGB + "'>" + displayNumber + "</th>");
    });

    listOfIndevScheme.forEach(item => {
      if (getBranchName(item) == branch_name) {
          var raw_score = (metrics[item] == undefined) ? "N/A" : round(metrics[item]);
          var bg_color = get_rgb(metrics[item+' score']);
          return_str += ("<th class='cell' style='" + bg_color + "'>" + raw_score + "</th>");
      }
    });

    return_str += "</tr>";
  }
  return_str += "</tbody>";

  return return_str;
}

function getIndevTable(branch_name) {
    var result = "<div style='overflow-x:auto;'><table id='indev-table-" + branch_name + "'>";
    //result += getIndevSchemeHeader(branch_name);
    //result += getIndevTableBody(branch_name);
    result += "</table></div><hr />";
    return result;
}

function createIndevTables() {
    var table_string = "";
    g_indev_branches.forEach(item => {
        table_string += getIndevTable(item);
    });
    document.getElementById('indev-scheme-tables').innerHTML = table_string;
}


function populateIndevScheme() {
  var tableHead = "<th class='description' style='text-decoration: none;'>Test Scenario</th>";
  var html_bracket = '<th class="cell" style="white-space:pre">';
  var html_bracket_end = '</th>';

    benchmarkSchemes.forEach(item => {
        tableHead += html_bracket;
        tableHead += item;
        tableHead += html_bracket_end;
    });

  listOfIndevScheme.forEach(item => {
    tableHead += html_bracket;
    var split = item.split(',');
    tableHead += split[0];
    tableHead += ':<br>';
    tableHead += split[1];
    tableHead += ':<br>';
    tableHead += split[2];
    tableHead += html_bracket_end;
  });
  document.getElementById('indev-scheme').innerHTML = tableHead;
}

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
  if (normalized_val >= 0.75) {
    green = 255;
  } else {
    green = 255 * (normalized_val / 0.75);
  }
  green = (0.9 * green) + 25;

  var red = 0;
  if (normalized_val <= 0.75) {
    red = 255;
  } else {
    red = 255 * (1 - normalized_val) / 0.25;
  }

  var blue = 0;
  if (normalized_val > 0.75) {
    blue = 255 * (normalized_val - 0.75) / 0.25;
  }
  blue = (0.9 * blue) + 25;
  return 'background-color: rgb(' + red + ',' + green + ',' + blue + ')'
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
    return_str += ("<th class='description'><a href=test_data/" + test_name + "/index.html>" + getDisplayName(curr_test) + "</a></th>");
    
    for (var j = 0; j < publicTestSchemes.length; j++) {
        var scheme = publicTestSchemes[j];
        var displayNumber = (metrics[scheme] == undefined) ? 'N/A' : round(metrics[scheme]);
        var displayRGB = get_rgb(metrics[scheme + " score"]);
        return_str += ("<th class='cell' style='" + displayRGB + "'>" + displayNumber + "</th>");
    }

    return_str += "</tr>";
  }

  return return_str;
}

function getBenchmarkTest(test_name) {
    for (var i = 0; i < json_data.Tests.length; i++) {
        if (json_data.Tests[i].name == test_name) {
            return json_data.Tests[i];
        }
    }
    return undefined;
}

function disp_power_metric() {
  var s = table_formatter('overall');
  document.getElementById("table-body").innerHTML = s;
  document.getElementById("metric-description").innerHTML = '<pre>Number: log(mean throughput / 95% delay) (Kleinrock\'s power metric)' +
  '<br>Color: log(mean throughput / 95% delay) / 7';
}

function disp_latency() {
  var s = table_formatter('95 qdelay');
  document.getElementById("table-body").innerHTML = s;
  document.getElementById("metric-description").innerHTML = '<pre>Number: 95% queueing delay among all tests, in ms' +
  '<br>Color: 1 - (95% delay / 60ms)';
}

function disp_thpt() {
  var s = table_formatter('avg thrput');
  document.getElementById("table-body").innerHTML = s;
  document.getElementById("metric-description").innerHTML = '<pre>Number: Mean throughput among all tests, in Mbps' +
  '<br>Color: Mean throughput / link bottleneck';
}

function disp_loss() {
  var s = table_formatter('avg loss');
  document.getElementById("table-body").innerHTML = s;
  document.getElementById("metric-description").innerHTML = '<pre>Number: Mean fraction of packets lost' +
  '<br>Color: 1 - 10*( (measured loss - random loss) / (1 - random loss) )';
}

var g_score_descriptions = {
    'avg thrput':'<pre>Number: Mean throughput among all tests, in Mbps'
                + '<br>Color: Mean throughput / link bottleneck',
    '95 qdelay':'<pre>Number: 95% queueing delay among all tests, in ms'
              + '<br>Color: 1 - (95% delay / 60ms)',
    'avg loss': '<pre>Number: Mean fraction of packets lost'
              + '<br>Color: 1 - 10*( (measured loss - random loss) / (1 - random loss) )',
    'overall': '<pre>Number: log(mean throughput / 95% delay) (Kleinrock\'s power metric)'
             + '<br>Color: log(mean throughput / 95% delay) / 5'
};

function disp_indev_scores(score_type) {
    document.getElementById("metric-description").innerHTML = g_score_descriptions[score_type];
    g_indev_branches.forEach(branch_name => {
        var result = getIndevSchemeHeader(branch_name);
        result += getIndevTableBody(branch_name, score_type);
        document.getElementById("indev-table-" + branch_name).innerHTML = result;
    });
}

function saveData(key,value) {
  localStorage.setItem(key,value) || (document.cookie = key + "=" + value);
}

function getData(key) {
  return localStorage.getItem(key) || document.cookie.match(new RegExp(key + "\=(.+?)(?=;)"))[1];
}
