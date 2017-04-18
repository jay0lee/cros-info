// Copyright (c) 2014 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

document.addEventListener('DOMContentLoaded', function() {
  if (typeof chrome.enterprise == 'undefined' || typeof chrome.enterprise.deviceAttributes == 'undefined') {
    
  }
  chrome.enterprise.deviceAttributes.getDirectoryDeviceId(function (deviceid) {
                console.log('Getting Device Id...');
                console.log('Device Id: ' + deviceid);
                chrome.storage.managed.get('primary_domain', function(primary_domain) {
                  console.log('Managed Storage Domain: ' + primary_domain.primary_domain);
                  chrome.identity.getProfileUserInfo(function(user_info) {
                    identity_domain = user_info["email"].split("@")[1];
                    console.log('Identity Domain: ' + identity_domain);
                    if (typeof primary_domain.primary_domain == 'undefined') {
                      use_domain = identity_domain;
                    } else {
                      use_domain = primary_domain.primary_domain;
                    };
                    appengine_url = 'https://cros-info.appspot.com/?primary_domain=' + use_domain + '&deviceid=' + deviceid;
                    console.log("URL: " + appengine_url);
                    document.getElementById("appengine").src = appengine_url;
                    })
                  });
  });
});
