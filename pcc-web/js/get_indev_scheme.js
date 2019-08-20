var listOfIndevScheme = new Set();

$.getJSON('metrics.json', function(data) {
  Object.keys(data).forEach(item => {
    //console.log(item);
    if (item.includes(',')) {
        listOfIndevScheme.add(item);
    }
  });
});
