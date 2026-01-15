# JDownloader 2 API Reference (Local Mode)

This document serves as a knowledge base for the JDownloader 2 API endpoints interacting with the JDownloader Manager.
It reflects the "Direct Connection" API (port 3128/9666), typically accessible via `http://localhost:3128` or `http://localhost:9666`.

**Note:** This local API often uses specific namespaces and camelCase formatting different from the general MyJDownloader REST API documentation found online.

## System Limits
| Action | Endpoint | Method | Params | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Restart** | `/system/restartJD` | POST | None | Restart the JDownloader application. |
| **Shutdown** | `/system/exitJD` | POST | None | Shutdown/Exit the JDownloader application. |
| **Ping/Help** | `/help` | GET | None | Returns list of available namespaces/methods. Used for connection check. |

## Downloads (downloadsV2)
| Action | Endpoint | Method | Params | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Query Packages** | `/downloadsV2/queryPackages` | POST | *QueryDict* | Get list of download packages. |
| **Query Links** | `/downloadsV2/queryLinks` | POST | *QueryDict* | Get list of links within packages. |
| **Remove Links** | `/downloadsV2/removeLinks` | POST | `{"params": [[linkIds], [packageIds]]}` | Delete packages or links. |

## LinkGrabber (linkgrabberv2)
| Action | Endpoint | Method | Params | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Query Packages** | `/linkgrabberv2/queryPackages` | POST | *QueryDict* | Get buffered packages. |
| **Query Links** | `/linkgrabberv2/queryLinks` | POST | *QueryDict* | Get buffered links. |
| **Add Links** | `/linkgrabberv2/addLinks` | POST | `{"links": "...", "autostart": bool}` | Add URLs to LinkGrabber. |
| **Add Container** | `/linkgrabberv2/addContainer` | POST | `{"params": ["DLC", content_str]}` | Add DLC/Container file. content often Base64. |
| **Move to DL** | `/linkgrabberv2/moveToDownloadlist` | POST | `{"params": [[linkIds], [packageIds]]}` | Confirm/Move items to download list. |
| **Remove** | `/linkgrabberv2/removeLinks` | POST | `{"params": [[linkIds], [packageIds]]}` | Delete items from grabber. |
| **Set Directory** | `/linkgrabberv2/setDownloadDirectory` | POST | `{"params": ["path", [packageIds]]}` | Change download path for packages. |

## Download Controller (downloadcontroller)
| Action | Endpoint | Method | Params | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Start** | `/downloadcontroller/start` | POST | None | Start downloads. |
| **Stop** | `/downloadcontroller/stop` | POST | None | Stop downloads. |

## Known Quirks
- **RPC Style:** Many endpoints (especially `v2`) expect a JSON payload with a `params` array corresponding to the Java method signature.
- **CamelCase:** System endpoints like `restartJD` and `exitJD` are case-sensitive and specific.
- **Legacy Fallback:** Some endpoints might be accessible via `linkcollector/*` but `linkgrabberv2/*` is preferred.

## Configuration (config)
The `config` namespace allows accessing internal JDownloader settings via RPC.
**Endpoint:** `/config/get`  
**Method:** POST  
**Payload:** `{"params": ["InterfaceName", null, "Key"]}`

### Check MyJDownloader Status
To check the connection status, query `MyJDownloaderSettings`.
- **Interface:** `org.jdownloader.api.myjdownloader.MyJDownloaderSettings`
- **Key:** `LatestError` (Returns `NONE` or `{}` if no error)
- **Key:** `DeviceName` (Returns configured device name)
- **Key:** `AutoConnectEnabledV2` (Returns boolean)

> [!IMPORTANT]
> **Live Status Verification**: The keys above only reflect the *configuration* and *last known error*. They do **not** guarantee an active connection to the MyJDownloader cloud. 
> To definitively verify the "Online" status, it is recommended to also check for an established TCP connection to `api.jdownloader.org` or `my.jdownloader.org` on port 443. The `LatestError` key may remain empty even if the persistent connection is down.


