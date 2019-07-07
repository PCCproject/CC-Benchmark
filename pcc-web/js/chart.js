$.ajaxSetup({
async: false
});

function searchChart(name, dict) {
  var testname = name.split('-')[0];
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

function renderChartwithData(id, chartData, title, x_name, y_name) {
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
  var schemes = ['tcp', 'vivace'];
  var res = new Array();
  $.getJSON(jsonfile, function(data) {
    for (var i = 0; i < schemes.length; i++) {
      var scheme = schemes[i];
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
      // console.log(points);
    }
  });

  return res;
}

function getAllPointsWithExtension(dir, fileextension, x_axis, y_axis) {
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
        $.getJSON(filename, function(data) {
          for (var j = 0; j < flows.length; j++) {
            var legend = flows[j];

            if (legend.includes('-')) {
              legend = legend.split('-')[0];
            }
            var line = {
              type:'line',
              showInLegend: true,
              //toolTipContent: "<b>Time: </b>{x}<br/><b>Throughput: </b>{y}",
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
