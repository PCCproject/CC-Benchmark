var listOfIndevScheme = new Set();

$.getJSON('metrics.json', function(data) {
  Object.keys(data).forEach(item => {
    // console.log(item);
    var c = item[item.length - 6];
      if (c == ',') {
        listOfIndevScheme.add(item);
      }
  });
});