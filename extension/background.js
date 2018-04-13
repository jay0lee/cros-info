function getData() {

  // Get Managed Storage Items
  chrome.storage.managed.get(['primary_domain', 'fields'], function(values) {
    data.primary_domain = values.primary_domain;
    data.fields = values.fields;
    
    // Get identity domain if we didn't get managed storage
    if (typeof values.primary_domain == 'undefined') {
      chrome.identity.getProfileUserInfo(function(user_info) {
        identity_domain = user_info["email"].split("@")[1];
        console.log('Identity Domain: ' + identity_domain);
        if (typeof identity_domain != 'undefined') {
          data.primary_domain = identity_domain;
        }
      });
    }
  });

  // Get Directory API Device ID
  if (typeof chrome.enterprise == 'undefined' || typeof chrome.enterprise.deviceAttributes == 'undefined' || typeof chrome.enterprise.deviceAttributes.getDirectoryDeviceId == 'undefined') {
    data.deviceid = undefined;
  } else {
    chrome.enterprise.deviceAttributes.getDirectoryDeviceId(function (deviceid) {
      data.deviceid = deviceid;
    });
  }

}

chrome.extension.onMessage.addListener(function(request, sender, sendResponse) {
    sendResponse(data)
});

/*** Main ***/
var data = {};
getData();