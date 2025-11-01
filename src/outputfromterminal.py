apple@007s-Mac email_writer % python3 src/fix_linkedin_urls.py
============================================================
🔧 LINKEDIN URL FIXER
============================================================

📊 Malformed LinkedIn URLs found: 118

🔄 Fixing URLs...
✅ Malformed URLs remaining: 109
✅ Fixed: 9 URLs

📋 Sample of fixed URLs:
     Company Name                                 LinkedIn (company)
0   CoinMarketCap    https://www.linkedin.com/company/coinmarketcap/
1            Fuse  https://www.linkedin.com/company/fuseenergyhq/...
2            Fuse  https://www.linkedin.com/company/fuseenergyhq/...
3  Jari Solutions     https://www.linkedin.com/company/jari-company/
4  Jari Solutions     https://www.linkedin.com/company/jari-company/

💾 Saving corrected CSV...
✅ Saved to: /Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/complete list.csv
============================================================
✅ DONE!
============================================================
apple@007s-Mac email_writer % python3 src/analyze_failures.py
============================================================
📊 FAILURE ANALYSIS
============================================================
Total companies missing industry: 151

Breakdown:
  ✅ Have LinkedIn URL but failed to scrape industry: 20
  🌐 Have Website but no LinkedIn URL found: 17
  ❌ Have nothing (no website, no LinkedIn): 114
============================================================

🔍 Sample companies WITH LinkedIn but NO industry:
     Company Name                              LinkedIn (company)
199   teamairship  https://www.linkedin.com/company//airship-llc/
203  SigaoStudios       https://www.linkedin.com/company/10703081
204  SigaoStudios       https://www.linkedin.com/company/10703081
216       iCodice       https://www.linkedin.com/company/icodice/
217       iCodice       https://www.linkedin.com/company/icodice/

🔍 Sample companies WITH Website but NO LinkedIn:
               Company Name                   Website
189                  Alesig       https://alesig.com/
200             teamairship  https://teamairship.com/
201             teamairship  https://teamairship.com/
955   a & d medical billing        https://andmed.net
1172       KawasakiRobotics        https://kri-us.com
apple@007s-Mac email_writer % python3 src/fill_industries.py
/Users/apple/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(

--- Pass 1: Finding/Fixing LinkedIn URLs from Websites ---
Found 131 companies to check for LinkedIn URL fixes.
  Processing (1/131): nan
    -> Skipping, invalid website URL: ''
  Processing (2/131): nan
    -> Skipping, invalid website URL: ''
  Processing (3/131): Alesig
    -> Could not fetch website https://alesig.com/. Error: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
  Processing (4/131): teamairship
    -> No LinkedIn company link found on website.
  Processing (5/131): teamairship
    -> No LinkedIn company link found on website.
  Processing (6/131): nan
    -> Skipping, invalid website URL: ''
  Processing (7/131): WEHRLE-WERK AG
    -> Skipping, invalid website URL: ''
  Processing (8/131): AGT International Investments
    -> Skipping, invalid website URL: ''
  Processing (9/131): Cumulocity
    -> Skipping, invalid website URL: ''
  Processing (10/131): nan
    -> Skipping, invalid website URL: ''
  Processing (11/131): AccuStrata
    -> Skipping, invalid website URL: ''
  Processing (12/131): BGA Technology LLC
    -> Skipping, invalid website URL: ''
  Processing (13/131): Industrial Ecosystems Partners
    -> Skipping, invalid website URL: ''
  Processing (14/131): nan
    -> Skipping, invalid website URL: ''
  Processing (15/131): nan
    -> Skipping, invalid website URL: ''
  Processing (16/131): nan
    -> Skipping, invalid website URL: ''
  Processing (17/131): nan
    -> Skipping, invalid website URL: ''
  Processing (18/131): nan
    -> Skipping, invalid website URL: ''
  Processing (19/131): nan
    -> Skipping, invalid website URL: ''
  Processing (20/131): nan
    -> Skipping, invalid website URL: ''
  Processing (21/131): Marshall Resources
    -> Skipping, invalid website URL: ''
  Processing (22/131): nan
    -> Skipping, invalid website URL: ''
  Processing (23/131): Apollo America
    -> Skipping, invalid website URL: ''
  Processing (24/131): nan
    -> Skipping, invalid website URL: ''
  Processing (25/131): nan
    -> Skipping, invalid website URL: ''
  Processing (26/131): nan
    -> Skipping, invalid website URL: ''
  Processing (27/131): a & d medical billing
    -> No LinkedIn company link found on website.
  Processing (28/131): nan
    -> Skipping, invalid website URL: ''
  Processing (29/131): nan
    -> Skipping, invalid website URL: ''
  Processing (30/131): nan
    -> Skipping, invalid website URL: ''
  Processing (31/131): KawasakiRobotics
    -> Could not fetch website https://kri-us.com. Error: HTTPSConnectionPool(host='kri-us.com', port=443): Max retries exceeded with url: / (Caused by ConnectTimeoutError(<urllib3.connection.HTTPSConnection object at 0x1148a8b50>, 'Connection to kri-us.com timed out. (connect timeout=20)'))
  Processing (32/131): nan
    -> Skipping, invalid website URL: ''
  Processing (33/131): nan
    -> Skipping, invalid website URL: ''
  Processing (34/131): nan
    -> Skipping, invalid website URL: ''
  Processing (35/131): nan
    -> Skipping, invalid website URL: ''
  Processing (36/131): VS Edventures
    -> Skipping, invalid website URL: ''
  Processing (37/131): nan
    -> Skipping, invalid website URL: ''
  Processing (38/131): nan
    -> Skipping, invalid website URL: ''
  Processing (39/131): nan
    -> Skipping, invalid website URL: ''
  Processing (40/131): nan
    -> Skipping, invalid website URL: ''
  Processing (41/131): nan
    -> Skipping, invalid website URL: ''
  Processing (42/131): nan
    -> Skipping, invalid website URL: ''
  Processing (43/131): nan
    -> Skipping, invalid website URL: ''
  Processing (44/131): nan
    -> Skipping, invalid website URL: ''
  Processing (45/131): nan
    -> Skipping, invalid website URL: ''
  Processing (46/131): nan
    -> Skipping, invalid website URL: ''
  Processing (47/131): nan
    -> Skipping, invalid website URL: ''
  Processing (48/131): nan
    -> Skipping, invalid website URL: ''
  Processing (49/131): nan
    -> Skipping, invalid website URL: ''
  Processing (50/131): nan
    -> Skipping, invalid website URL: ''
  Processing (51/131): nan
    -> Skipping, invalid website URL: ''
  Processing (52/131): nan
    -> Skipping, invalid website URL: ''
  Processing (53/131): nan
    -> Skipping, invalid website URL: ''
  Processing (54/131): nan
    -> Skipping, invalid website URL: ''
  Processing (55/131): Innovation Energy Technology
    -> Could not fetch website https://jsenergyusa.com. Error: HTTPSConnectionPool(host='jsenergyusa.com', port=443): Max retries exceeded with url: / (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x115227c10>: Failed to resolve 'jsenergyusa.com' ([Errno 8] nodename nor servname provided, or not known)"))
  Processing (56/131): nan
    -> Skipping, invalid website URL: ''
  Processing (57/131): nan
    -> Skipping, invalid website URL: ''
  Processing (58/131): nan
    -> Skipping, invalid website URL: ''
  Processing (59/131): nan
    -> Skipping, invalid website URL: ''
  Processing (60/131): nan
    -> Skipping, invalid website URL: ''
  Processing (61/131): nan
    -> Skipping, invalid website URL: ''
  Processing (62/131): nan
    -> Skipping, invalid website URL: ''
  Processing (63/131): nan
    -> Skipping, invalid website URL: ''
  Processing (64/131): nan
    -> Skipping, invalid website URL: ''
  Processing (65/131): nan
    -> Skipping, invalid website URL: ''
  Processing (66/131): Nofar Energy Israel
    -> Skipping, invalid website URL: ''
  Processing (67/131): nan
    -> Skipping, invalid website URL: ''
  Processing (68/131): nan
    -> Skipping, invalid website URL: ''
  Processing (69/131): Blue ocean global
    -> Skipping, invalid website URL: ''
  Processing (70/131): nan
    -> Skipping, invalid website URL: ''
  Processing (71/131): nan
    -> Skipping, invalid website URL: ''
  Processing (72/131): nan
    -> Skipping, invalid website URL: ''
  Processing (73/131): nan
    -> Skipping, invalid website URL: ''
  Processing (74/131): nan
    -> Skipping, invalid website URL: ''
  Processing (75/131): nan
    -> Skipping, invalid website URL: ''
  Processing (76/131): nan
    -> Skipping, invalid website URL: ''
  Processing (77/131): nan
    -> Skipping, invalid website URL: ''
  Processing (78/131): nan
    -> Skipping, invalid website URL: ''
  Processing (79/131): nan
    -> Skipping, invalid website URL: ''
  Processing (80/131): nan
    -> Skipping, invalid website URL: ''
  Processing (81/131): nan
    -> Skipping, invalid website URL: ''
  Processing (82/131): nan
    -> Skipping, invalid website URL: ''
  Processing (83/131): Motiv Power Systems
    -> Could not fetch website https://motivps.com. Error: 403 Client Error: Forbidden for url: https://motivps.com/
  Processing (84/131): Motiv Power Systems
    -> Could not fetch website https://motivps.com. Error: 403 Client Error: Forbidden for url: https://motivps.com/
  Processing (85/131): Motiv Power Systems
    -> Could not fetch website https://motivps.com. Error: 403 Client Error: Forbidden for url: https://motivps.com/
  Processing (86/131): Motiv Power Systems
    -> Could not fetch website https://motivps.com. Error: 403 Client Error: Forbidden for url: https://motivps.com/
  Processing (87/131): nan
    -> Skipping, invalid website URL: ''
  Processing (88/131): nan
    -> Skipping, invalid website URL: ''
  Processing (89/131): Motiv Power Systems
    -> Could not fetch website https://motivps.com. Error: 403 Client Error: Forbidden for url: https://motivps.com/
  Processing (90/131): Motiv Power Systems
    -> Could not fetch website https://motivps.com. Error: 403 Client Error: Forbidden for url: https://motivps.com/
  Processing (91/131): nan
    -> Skipping, invalid website URL: ''
  Processing (92/131): nan
    -> Skipping, invalid website URL: ''
  Processing (93/131): nan
    -> Skipping, invalid website URL: ''
  Processing (94/131): nan
    -> Skipping, invalid website URL: ''
  Processing (95/131): nan
    -> Skipping, invalid website URL: ''
  Processing (96/131): JLab
    -> Skipping, invalid website URL: ''
  Processing (97/131): nan
    -> Skipping, invalid website URL: ''
  Processing (98/131): Swissten
    -> No LinkedIn company link found on website.
  Processing (99/131): Swissten
    -> No LinkedIn company link found on website.
  Processing (100/131): Swissten
    -> No LinkedIn company link found on website.
  Processing (101/131): nan
    -> Skipping, invalid website URL: ''
  Processing (102/131): Bossard Ireland
    -> No LinkedIn company link found on website.
  Processing (103/131): nan
    -> Skipping, invalid website URL: ''
  Processing (104/131): nan
    -> Skipping, invalid website URL: ''
  Processing (105/131): nan
    -> Skipping, invalid website URL: ''
  Processing (106/131): nan
    -> Skipping, invalid website URL: ''
  Processing (107/131): nan
    -> Skipping, invalid website URL: ''
  Processing (108/131): ETO GRUPPE TECHNOLOGIES GmbH
    -> Skipping, invalid website URL: ''
  Processing (109/131): ETO Magnetic GmbH
    -> Skipping, invalid website URL: ''
  Processing (110/131): MEKRA Lang Gmbh&Co.KG
    -> Skipping, invalid website URL: ''
  Processing (111/131): nan
    -> Skipping, invalid website URL: ''
  Processing (112/131): nan
    -> Skipping, invalid website URL: ''
  Processing (113/131): nan
    -> Skipping, invalid website URL: ''
  Processing (114/131): nan
    -> Skipping, invalid website URL: ''
  Processing (115/131): APB SISTEMAS Y CONTROL DE ACCESOS SA DE CV
    -> No LinkedIn company link found on website.
  Processing (116/131): Clearview Communications
    -> Skipping, invalid website URL: ''
  Processing (117/131): SALTO SYSTEMS
    -> Skipping, invalid website URL: ''
  Processing (118/131): TKH Security Solutions USA
    -> Skipping, invalid website URL: ''
  Processing (119/131): nan
    -> Skipping, invalid website URL: ''
  Processing (120/131): nan
    -> Skipping, invalid website URL: ''
  Processing (121/131): nan
    -> Skipping, invalid website URL: ''
  Processing (122/131): HB Hekwerk Oost
    -> Skipping, invalid website URL: ''
  Processing (123/131): nan
    -> Skipping, invalid website URL: ''
  Processing (124/131): nan
    -> Skipping, invalid website URL: ''
  Processing (125/131): ADT Fire & Security
    -> Skipping, invalid website URL: ''
  Processing (126/131): nan
    -> Skipping, invalid website URL: ''
  Processing (127/131): nan
    -> Skipping, invalid website URL: ''
  Processing (128/131): nan
    -> Skipping, invalid website URL: ''
  Processing (129/131): nan
    -> Skipping, invalid website URL: ''
  Processing (130/131): nan
    -> Skipping, invalid website URL: ''
  Processing (131/131): nan
    -> Skipping, invalid website URL: ''
Pass 1 complete. Found and updated 0 LinkedIn URLs.

--- Pass 2: Scraping Industries from LinkedIn URLs ---
Found 20 companies to process for industry.
  Processing (1/20): teamairship
    -> Could not fetch URL https://www.linkedin.com/company//airship-llc/. Error: 404 Client Error: Not Found for url: https://www.linkedin.com/company//airship-llc/
  Processing (2/20): SigaoStudios
    -> Industry not found on page.
  Processing (3/20): SigaoStudios
    -> Industry not found on page.
  Processing (4/20): iCodice
    -> Found Industry: Software Development
  Processing (5/20): iCodice
    -> Found Industry: Software Development
  Processing (6/20): Rockstar Coders
    -> Found Industry: IT Services and IT Consulting
  Processing (7/20): Rockstar Coders
    -> Found Industry: IT Services and IT Consulting
  Processing (8/20): Rockstar Coders
    -> Found Industry: IT Services and IT Consulting
  Processing (9/20): Rockstar Coders
    -> Found Industry: IT Services and IT Consulting
  Processing (10/20): Carminati Consulting, Inc.
    -> Could not fetch URL https://www.linkedin.com/company/carminati-consulting-inc/. Error: 404 Client Error: Not Found for url: https://www.linkedin.com/company/carminati-consulting-inc/
  Processing (11/20): Carminati Consulting, Inc.
    -> Could not fetch URL https://www.linkedin.com/company/carminati-consulting-inc/. Error: 404 Client Error: Not Found for url: https://www.linkedin.com/company/carminati-consulting-inc/
  Processing (12/20): WSP, Inc.
    -> Industry not found on page.
  Processing (13/20): WSP, Inc.
    -> Industry not found on page.
  Processing (14/20): Joint, Clutch & Gear Service, Inc.
    -> Industry not found on page.
  Processing (15/20): NMDC- Energy ( formerly NPCC )
    -> Industry not found on page.
  Processing (16/20): IGB
    -> Industry not found on page.
  Processing (17/20): Pluto LLC
    -> Industry not found on page.
  Processing (18/20): FronTone
    -> Industry not found on page.
  Processing (19/20): Shelby Interactive, LLC
    -> Industry not found on page.
  Processing (20/20): Bosch eBike Systems
    -> Industry not found on page.
Pass 2 complete. Found and updated 6 industries.

--- Saving Final Results ---
Saving updated data back to /Users/apple/Downloads/Automation projects/AI agent/Dashcam AI agent/email_writer/data/Companies/complete list.csv...
File saved successfully.
apple@007s-Mac email_writer % 
