$.ajaxSetup({
async: false
});

const public_scheme = new Set(['copa', 'vivace_latency', 'default_tcp', 'bbr']);

function searchChart(name, dict) {
  // console.log(dict);
  var testname = name.split('-')[0];
  // console.log(testname);
  return dict[testname];
}

function getNumTrials(titles) {
  var ret = {};
  for (var i = 0; i < titles.length; i++) {
    var title = titles[i];
    title = title.split('-')[0];
    if (ret.hasOwnProperty(title)) {
      ret[title] += 1;
    } else {
      ret[title] = 1;
    }
  }
  return ret;
}

function getIndexOfDataPoints(target, titles) {
  for (var i = 0; i < titles.length; i++) {
    if (titles[i].split('.')[0] == target) {
      return i;
    }
  }
}

function renderRttFairnessChart(id, chartData) {
  var chart = new CanvasJS.Chart(id, {
    animationEnabled: true,
    zoomEnabled: true,
    title: {
      text: "Fairness Metrics"
    },
    axisX: {
      title: "Rtt Ratio",
      minimum: 0
    },
    axisY: {
      title: "Jain's Fairness Index",
      maximum: 1.1
    },
    data: chartData,
  });
  chart.render();
}

function parseDateTime(datetime) {
  var monthToVal = {
    "January":1,
    "February":2,
    "March":3,
    "April":4,
    "May":5,
    "June":6,
    "July":7,
    "August":8,
    "September":9,
    "October":10,
    "November":11,
    "December":12
  };
  datetime = datetime.split('_');
  month = parseInt(monthToVal[datetime[0]]);
  day = parseInt(datetime[1]);
  year = parseInt(datetime[2]);
  sec = parseInt(datetime[3]);

  return [year, month, day, sec];
}

function sortTime(a, b) {
  var t1 = parseDateTime(a);
  var t2 = parseDateTime(b);

  if (t1[0] > t2[0]) {
    return 1;
  }
  if (t1[0] < t2[0]) {
    return -1;
  }
  if (t1[1] > t2[1]) {
    return 1;
  }
  if (t1[1] < t2[1]) {
    return -1;
  }
  if (t1[2] > t2[2]) {
    return 1;
  }
  if (t1[2] < t2[2]) {
    return -1;
  }
  if (t1[3] > t2[3]) {
    return 1;
  }
  if (t1[3] < t2[3]) {
    return -1;
  }

  return 0;
}

function getMatchingIdx(titles, target) {
  for (var i = 0; i < titles.length; i++) {
    if (titles[i] === target) {
      return i;
    }
  }
  return -1;
}
function getTestTrials(titles) {
  var res = {};
  for (var i = 0; i < titles.length; i++) {
    var split = titles[i].split('-');
    var testid = split[0];
    var detail = split[1].split('.json')[0];
    if (!res.hasOwnProperty(testid)) {
      res[testid] = [];
    }
    res[testid].push(detail);
  }
  var keys = Object.keys(res);

  for (var i = 0; i < keys.length; i++) {
    res[keys[i]].sort(sortTime);
  }

  return res
}

function renderChartwithData(id, chartData, title, x_name, y_name) {
  // console.log(id);
  var chart = new CanvasJS.Chart(id, {
    animationEnabled: true,
    zoomEnabled: true,
    title: {
      text: title
    },
    axisX: {
      // title: "Time(ms)",
      title: x_name,
      minimum: 0,
    },
    axisY: {
      // title: "Throughput",
      title: y_name,
      minimum: 0
    },
    data: chartData,
    options: {
        elements: {
            point: {
                radius: 0,
                hitRadius: 1,
                hoverRadius: 1
            }
        }
    }
  });
  chart.render();

  return chart;
}

function getMetricCoordForSingleScheme(data, testname) {
  var res1 = [];
  var res2 = [];
  for (var name in data) {
    var x = undefined;
    if (testname == undefined) {
      x = parseFloat(name);
    } else if (testname.includes("rtt")) {
      var split = name.split('_to_');
      x = parseFloat(split[1]) / parseFloat(split[0])
    } else if (testname.includes('jitter')) {
      var split = name.split('_');
      x = parseFloat(split[1]);
    }

    var linkUtil = data[name]['Avg Thrput'];
    var delay = data[name]['95 Queue Delay'];
    res1.push({
      'x': x,
      'y': linkUtil
    });
    res2.push({
      'x': x,
      'y': delay
    });
  }

  return new Array(res1, res2);
}


function getPublicLinkUtilAndQueueingDelay(jsonfile, testname) {
  var res = {};
  $.getJSON(jsonfile, function(data) {
    for (var scheme in data) {
      if (public_scheme.has(scheme)) {
        var dataPoint = getMetricCoordForSingleScheme(data[scheme], testname);
        res[scheme] = dataPoint;
      }
    }
  });

  var utilData = new Array();
  var delayData = new Array();
  for (var scheme in res) {
    var utilPoints = [];
    var delayPoints = [];
    for (var j = 0; j < res[scheme][0].length; j++) {
      utilPoints.push({
        x: res[scheme][0][j]['x'],
        y: res[scheme][0][j]['y']
      });
      delayPoints.push({
        x: res[scheme][1][j]['x'],
        y: res[scheme][1][j]['y']
      });
    }

    utilData.push({
      type:'scatter',
      showInLegend: true,
      toolTipContent: "<b>x: </b>{x}<br/><b>y: </b>{y}",
      legendText: scheme,
      dataPoints: utilPoints
    });

    delayData.push({
      type:'scatter',
      showInLegend: true,
      toolTipContent: "<b>x: </b>{x}<br/><b>y: </b>{y}",
      legendText: scheme,
      dataPoints: delayPoints
    });
  }

  return new Array(utilData, delayData);
}

function getJainIndexCoord(jsonfile) {
  var res = new Array();
  $.getJSON(jsonfile, function(data) {
    // console.log(data)
    for (var scheme in data) {
      var dataPoints = data[scheme];
      var points = [];
      for (var j = 0; j < dataPoints.length; j++) {
        var coord = {
          x: dataPoints[j]["x"],
          y: dataPoints[j]["y"]
        }
        points.push(coord);
      }
      res.push({
        type:'scatter',
        showInLegend: true,
        toolTipContent: "<b>Rtt Ratio: </b>{x}<br/><b>Jain's Fairness Index: </b>{y}",
        legendText: scheme,
        dataPoints: points
      });
    }
  });

  return res;
}

function getAllDataPointsFileLoc(dir) {
  var files = new Array();
  $.ajax({
    url: dir,
    async: false,
    success: function(data) {
      var split = data.split('Parent Directory')[1].split('href=\"');
      for (var i = 1; i < split.length; i++) {
        var file = split[i].split('\">')[0];
        if (file.includes('metric-')) {
          files.push(split[i].split('metric-')[1].split('\">')[0]);
        }
      }
    }
  });
  return files;
}

function getNumFlows(data) {
  var i = 1;
  while (true) {
    if (data.hasOwnProperty('flow'+i)) {
      i += 1;
    } else {
      break;
    }
  }
  return i - 1;
}

function getAllPoints(dir) {
  var allFileName = getAllDataPointsFileLoc(dir);
  var files = new Array();
  var files2 = new Array();
  for (let i in allFileName) {
    var filename = dir + '/' + allFileName[i];
    var thrput_points = new Array();
    var lat_points = new Array();
    var flows = allFileName[i].split(".json")[0].split("_to_");
    $.getJSON(filename, function(data) {
      for (var j = 0; j < flows.length; j++) {
        var legend = flows[j];

        if (legend.includes('-')) {
          legend = legend.split('-')[0];
        }

        var thrput_line = {
          type:'line',
          showInLegend: true,
          toolTipContent: "<b>Time(ms): </b>{x}<br/><b>Throughput(Mbps): </b>{y}",
          legendText: legend,
          dataPoints: []
        }

        var lat_line = {
          type:'line',
          showInLegend: true,
          toolTipContent: "<b>Time(ms): </b>{x}<br/><b>Latency(ms): </b>{y}",
          legendText: legend,
          dataPoints: []
        }

        var allFlowPoint = data['flow'+(j+1)];
        for (var k = 0; k < allFlowPoint.length; k++) {
          var currData = allFlowPoint[k];
          var thrput_loc = {
            x: currData["Time"],
            y: currData["Throughput"]
          }

          var lat_loc = {
            x: currData["Time"],
            y: currData["Avg Rtt"]
          }
          thrput_line.dataPoints.push(thrput_loc);
          lat_line.dataPoints.push(lat_loc);
        }
        thrput_points.push(thrput_line);
        lat_points.push(lat_line);
      }

    });
    files.push({"title": allFileName[i], "dataPoints": thrput_points});
    files2.push({"title": allFileName[i], "dataPoints": lat_points});
  }
  return [files, files2];
}

function getXAndYCoordFromJson(jsonfile) {
  var points = [];
  $.getJSON(jsonfile, function(data) {
    var allData = data["data"];
    for (var i = 0; i < allData.length; i++) {
      var currData = allData[i];
      var loc = {
        x: currData["x"],
        y: currData["y"]
      }
      points.push(loc);
    }
  });

  return points;
}

$(window).scroll(function() {
    if ($(this).scrollTop() > 50 ) {
        $('.scrolltop:hidden').stop(true, true).fadeIn();
    } else {
        $('.scrolltop').stop(true, true).fadeOut();
    }
});
$(function(){$(".scroll").click(function(){$("html,body").animate({scrollTop:$(".thetop").offset().top},"1000");return false})})
