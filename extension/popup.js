function dictToURI(dict) {
  var str = [];
  for(var p in dict){
     str.push(encodeURIComponent(p) + "=" + encodeURIComponent(dict[p]));
  }
  return str.join("&");
}

document.onreadystatechange = function () {
  if (document.readyState === "interactive") {
    chrome.extension.sendMessage({}, function(data) {
      appengine_url = 'https://cros-info.appspot.com/?' +
          dictToURI(data);
      console.log("URL: " + appengine_url);
      document.getElementById("appengine").src = appengine_url;
    });
  }
};