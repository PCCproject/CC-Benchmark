$.ajaxSetup({
async: false
});

function searchChart(name, dict) {
  console.log(dict);
  var testname = name.split('-')[0];
  console.log(testname);
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
    // console.log(testid);
    // console.log(detail);
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
                hitRadius: 10,
                hoverRadius: 10
            }
        }
    }
  });
  chart.render();

  return chart;
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

function getAllPointsWithExtensionRtt(dir, fileextension, x_axis, y_axis) {
  var files = new Array();
  $.ajax({
    url: dir,
    async: false,
    success: function(data) {
      $(data).find("a:contains(" + fileextension + ")").each(function() {
        var filename = this.href.replace(window.location.host, "").replace("http://", "");
        var file = filename.split("/");
        var name = file[file.length - 1];
        flows = name.split(".json")[0].split("_to_");
        var i = 1
        var points = new Array();
        if (!filename.includes('metric')) {
          $.getJSON(filename, function(data) {
            for (var j = 0; j < flows.length; j++) {
              var legend = flows[j];

              if (legend.includes('-')) {
                legend = legend.split('-')[0];
              }
              var line = {
                type:'line',
                showInLegend: true,
                toolTipContent: "<b>Time(ms): </b>{x}<br/><b>Throughput(kbps): </b>{y}",
                legendText: legend,
                dataPoints: []
              }

              var allFlowPoint = data['flow'+i];
              // console.log(allFlowPoint.length);
              for (var k = 0; k < allFlowPoint.length; k++) {
                var currData = allFlowPoint[k];
                // console.log(currData);
                var loc = {
                  x: currData[x_axis],
                  y: currData[y_axis]
                }
                line.dataPoints.push(loc);
              }
              i += 1;
              points.push(line);
            }

          });
          // console.log(points);
          files.push({"title": name, "dataPoints": points});
        }
      });
    }
  });
  return files;
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
