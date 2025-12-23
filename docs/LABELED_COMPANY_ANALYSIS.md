# Labeled Company Analysis - Product Categories

## Executive Summary

**Total Labeled Companies**: 35 unique companies (334 contact records)

**Product Distribution**:
- **Dashcam/In-Cabin**: 18 companies (51%)
- **Access Control/IP Camera**: 12 companies (34%)  
- **Beacon**: 5 companies (14%)

---

## 1. ACCESS CONTROL / IP CAMERA (12 companies)

### ✅ **Clear Pattern Identified:**

**What these companies do:**
- Physical security systems (cameras, access control, alarms)
- Smart home/building security platforms
- Cloud-based security management
- **NOT** general electronics or consumer products

**Key Industries:**
- Security & Investigations (50%)
- Information Technology & Services (33%)
- Electrical/Electronic Manufacturing (17%)

**Representative Examples:**
1. **Verkada** - Cloud-managed security cameras & access control ($806M revenue)
2. **Alarm.com** - Smart security platform with cameras/sensors ($955M revenue)
3. **Avigilon** - Video surveillance systems ($500M revenue)
4. **SimpliSafe** - Home security systems with cameras ($400M revenue)

**Common Characteristics:**
- ✅ ALL sell IP cameras or access control hardware
- ✅ ALL are security-focused companies
- ✅ Majority have cloud/software platforms for device management
- ✅ Revenue range: $27M - $1.9B
- ✅ All based in USA

**❌ FALSE POSITIVES TO AVOID:**
- General consumer electronics (TVs, appliances)
- Lighting companies (LED manufacturers like OSRAM)
- Lock manufacturers that don't have electronic access control
- Companies that only provide security guard services (no hardware)

---

## 2. DASHCAM / IN-CABIN (18 companies)

### ✅ **Clear Pattern Identified:**

**What these companies do:**
- Fleet management platforms with video telematics
- In-vehicle camera systems for commercial fleets
- Driver monitoring & safety systems
- Vehicle tracking with dashcam integration

**Key Industries:**
- Information Technology & Services (78%)
- Management Consulting (13%)
- Automotive (5%)

**Representative Examples:**
1. **Lytx** - Video telematics & driver safety ($300M revenue)
2. **Geotab** - Fleet management with dashcam support ($513M revenue)
3. **MiX Telematics** - Fleet tracking & in-cabin monitoring ($1.4B revenue)
4. **SmartEye** - Driver monitoring systems for automotive ($32M revenue)

**Common Characteristics:**
- ✅ Focus on **commercial fleets** (trucks, delivery, transport)
- ✅ Offer dashcams AND/OR in-cabin monitoring
- ✅ Often part of larger telematics/GPS tracking platform
- ✅ Geographic diversity (UK, USA, Canada, South Africa, Sweden)
- ✅ Revenue range: $3M - $6.4B

**Sub-Categories:**
1. **Fleet Telematics** (12 companies): Geotab, Fleet Complete, MiX Telematics
2. **Dashcam-Specific** (3 companies): Nexar, Cobra Electronics, HD Fleet
3. **Driver Monitoring** (3 companies): Smart Eye, SureCam, Lytx

**❌ FALSE POSITIVES TO AVOID:**
- Personal dashcam retailers (no fleet focus)
- General automotive suppliers without camera products
- Navigation companies (Garmin was included but is borderline)
- Transportation companies that don't sell hardware

---

## 3. BEACON (5 companies)

### ✅ **Clear Pattern Identified:**

**What these companies do:**
- Cold storage warehouses
- Temperature-controlled logistics
- Companies that need asset tracking in warehouses/fridges

**Key Industries:**
- Warehousing (80%)
- Logistics & Supply Chain (20%)

**Representative Examples:**
1. **USA Cold Storage** - Cold storage warehouse operator ($480M revenue)
2. **VersaCold** - Temperature-controlled logistics ($370M revenue)
3. **Vertical Cold Storage** - Cold chain warehousing (400 employees)

**Common Characteristics:**
- ✅ ALL operate cold storage/refrigerated facilities
- ✅ Need beacons for **inventory tracking** in large warehouses
- ✅ Temperature monitoring is critical
- ✅ Based in North America (USA, Canada, Mexico)
- ✅ Revenue range: Not disclosed - $480M

**❌ FALSE POSITIVES TO AVOID:**
- Regular warehouses without IoT tracking needs
- Retail companies
- General logistics without warehouse operations
- Companies that only transport (not store)

---

## KEY INSIGHTS FOR MATCHING ALGORITHM

### 🎯 **Critical Success Factors:**

1. **For Access Control/IP Camera:**
   - MUST mention: "security", "surveillance", "access control", "IP camera", "video security"
   - Industry: "security & investigations" OR "electronic security"
   - ❌ Exclude: consumer electronics, lighting, general hardware

2. **For Dashcam/In-Cabin:**
   - MUST mention: "fleet", "telematics", "dashcam", "driver monitoring", "in-cabin", "commercial vehicles"  
   - Industry: "fleet management", "telematics", "automotive"
   - Focus: **Commercial/Enterprise** (not consumer)
   - ❌ Exclude: personal dashcam retailers, car manufacturers

3. **For Beacon:**
   - MUST mention: "warehouse", "cold storage", "refrigerated", "logistics", "asset tracking"
   - Industry: "warehousing", "logistics", "cold chain"
   - ❌ Exclude: retail, transportation-only, non-warehouse companies

### 🚫 **Universal Exclusions:**
- Software-only companies
- Pure consulting firms
- Distributors/resellers (no product ownership)
- Consumer electronics brands (TVs, appliances, lighting)
- Companies with products completely unrelated to cameras/IoT

---

## RECOMMENDATIONS FOR FIXING THE ANALYSIS SCRIPT

### Option 1: **Stricter Keyword Matching**
Add NEGATIVE keywords to filter out false positives:
- ❌ "television", "TV", "LED bulbs", "lighting solutions", "appliances"
- ❌ "physical locks", "padlock", "door hardware" (if no electronic component)

### Option 2: **Industry-Based Filtering**
Require companies to be in specific industries:
- **Access Control/IP Camera**: security & investigations, physical security, electronic security
- **Dashcam**: fleet management, telematics, automotive technology
- **Beacon**: warehousing, cold storage, logistics

### Option 3: **RAG Similarity Threshold**
Use the existing RAG system with STRICTER distance thresholds:
- Current: 150
- Proposed: 100 (tighter matching)

### Option 4: **Hybrid Approach** (RECOMMENDED)
1. RAG filters first (distance < 120)
2. LLM validates the match with strict criteria
3. Negative keyword check removes obvious false positives
4. Industry validation as final check

---

## NEXT STEPS

1. ✅ **Data validated** - 35 correctly labeled companies
2. ⏭️ **Update matching logic** based on these patterns
3. ⏭️ **Re-run analysis** on CES 2026 list
4. ⏭️ **Validate results** against these labeled examples
5. ⏭️ **Create "Body Cam" training set** (currently missing from labeled data)

**Note**: Body cam companies are NOT in this dataset yet. Need to add examples like:
- Axon (police body cams)
- Motorola Solutions (public safety body cams)
- Reveal Media
- Body Worn (Digital Barriers)
