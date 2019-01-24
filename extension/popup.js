var attribute_map = {
          'annotatedLocation': 'Location',
          'macAddress': 'WiFi MAC Address',
          'ethernetMacAddress': 'Ethernet MAC Address',
          'notes': 'Notes',
          'serialNumber': 'Serial Number',
          'annotatedUser': 'User',
          'model': 'Model',
          'annotatedAssetId': 'Asset ID',
          'orgUnitPath': 'Organization Unit',
          'bootMode': 'Boot Mode',
          'deviceId': 'Directory API ID',
          'firmwareVersion': 'Firmware Version',
          'lastEnrollmentTime': 'Enrollment Date',
          'lastSync': 'Last policy fetch time',
          'meid': 'MEID',
          'model': 'Model',
          'orderNumber': 'Order Number',
          'osVersion': 'Google Chrome Version',
          'platformVersion': 'Platform Version',
          'recentUsers': 'Recent Users',
          'status': 'Status',
          'supportEndDate': 'Support End Date',
          'willAutoRenew': 'Will Auto Renew'
};

// From https://www.chromium.org/chromium-os/tpm_firmware_update
var CROS_TPM_VULN_VERSIONS = ['41f',  '420', '628', '8520',];
var CROS_TPM_FIXED_VERSIONS = ['422', '62b', '8521',];

function dictToURI(dict) {
  var str = [];
  for(var p in dict){
     str.push(encodeURIComponent(p) + "=" + encodeURIComponent(dict[p]));
  }
  return str.join("&");
}

function addToTable(rows) {
  var table = document.getElementById("data");
  for ( var index in rows ) {
    var row = table.insertRow(-1);
    row.style = "white-space:nowrap";
    var cell1 = row.insertCell(0);
    var cell2 = row.insertCell(1);
    cell1.innerHTML = '<b>'+index+'</b>';
    cell2.innerHTML = rows[index];
  }
}

function getLocalIPs() { // thanks to https://stackoverflow.com/a/29514292
    var ips = [];
    var RTCPeerConnection = window.RTCPeerConnection ||
        window.webkitRTCPeerConnection || window.mozRTCPeerConnection;
    var pc = new RTCPeerConnection({ iceServers: [] });
    pc.createDataChannel('');
    pc.onicecandidate = function(e) {
        if (!e.candidate) {
            pc.close();
            addToTable({'IP Addresses': ips.join(', ')});
            return;
        }
        var ip = /^candidate:.+ (\S+) \d+ typ/.exec(e.candidate.candidate)[1];
        if (ips.indexOf(ip) == -1 && ip.substring(0, 11) != "100.115.92.") // ignore ARC++ and container IPs
            ips.push(ip);
    };
    pc.createOffer(function(sdp) {
        pc.setLocalDescription(sdp);
    }, function onerror() {});
}

document.onreadystatechange = function () {
  if (document.readyState === "interactive") {
    // Get Managed Storage Items
    chrome.storage.managed.get(['primary_domain', 'fields', 'remote_url'], function(values) {
      primary_domain = values.primary_domain;
      if (typeof values.primary_domain == 'undefined') {
        chrome.identity.getProfileUserInfo(function(user_info) {
          identity_domain = user_info["email"].split("@")[1];
          console.log('Identity Domain: ' + identity_domain);
          if (typeof identity_domain != 'undefined') {
            primary_domain = identity_domain;
          }
        });
      }
      remote_url = values.remote_url;
      if (typeof remote_url == 'undefined') {
        remote_url = 'https://cros-info.appspot.com/json';
      }
      fields = values.fields;
      if (typeof values.fields == 'undefined') {
        fields = 'annotatedAssetId,annotatedLocation,annotatedUser,ethernetMacAddress,ipAddresses,macAddress,model,notes,orgUnitPath,serialNumber,tpmVersionInfo/firmwareVersion';
      }
      fields = fields.split(',');
      var remote_data = [];
      fields.forEach(function(item) {
        switch ( item ) {
          case 'serialNumber':
            chrome.enterprise.deviceAttributes.getDeviceSerialNumber(function (sn) {
              addToTable({'Serial Number': sn});
            });
            break;
          case 'ipAddresses':
            getLocalIPs();
            break;
          case 'annotatedAssetId':
            chrome.enterprise.deviceAttributes.getDeviceAssetId(function(aid) {
              addToTable({'Asset ID': aid});
            });
            break;
          case 'annotatedLocation':
            chrome.enterprise.deviceAttributes.getDeviceAnnotatedLocation(function(loc) {
              addToTable({'Location': loc});
            });
            break;
          default:
            remote_data.push(item);
          }
      });
      if ( remote_data.length > 0 ) {
        chrome.enterprise.deviceAttributes.getDirectoryDeviceId(function (id) {
          params = dictToURI({'fields': remote_data, 'primary_domain': primary_domain, 'deviceid': id});
          appengine_url = remote_url + '?' + params;
          console.log("URL: " + appengine_url);
          fetch(appengine_url)
            .then((resp) => resp.json())
            .then(function(items) {
              if ( items.success === true ) {
                delete items.success;
                mapped_items = {}
                for ( var item in items ) {
                  if ( item === 'tpmVersionInfo' && 'firmwareVersion' in items.tpmVersionInfo ) {
                    fwver = items.tpmVersionInfo.firmwareVersion;
                    if ( fwver in CROS_TPM_VULN_VERSIONS ) {
                      mapped_items['TPM Vulnerability'] = '<font color="red">Vulnerable</font> - ' + fwver;
                    } else if ( fwver in CROS_TPM_FIXED_VERSIONS ) {
                      mapped_items['TPM Vulnerability'] = '<font color="green">Updated</font> - ' + fwver;
                    } else {
                      mapped_items['TPM Vulnerability'] = '<font color="green">Not Vulnerable</font> - ' + fwver;
                    }
                  }
                  if ( item in attribute_map ) {
                    mapped_items[attribute_map[item]] = items[item];
                  }
                };
                addToTable(mapped_items);
              }
            });
        });
      }
    }); 
  }
};

