# POLITICS CENSUS (Nov 11, 2026; Kalshi public API only)
PARLAYS: YES, combos exist but NOT in politics. GET /multivariate_event_collections lists 1,406 collections (series KXMVENBASINGLEGAME 1113, KXMVENFLSINGLEGAME 223, KXCITIESWEATHER 35, KXMVEMENTIONSSINGLE 13, NFL/NBA/sports multigame 14, KXMVECROSSCATEGORY 2 shards, Oscars/Grammys/CB championship). Fields: size_min 2, size_max (0 on cross-category), is_all_yes, is_ordered, associated_event_tickers. Market resolves YES only if every leg is YES. Cross-category associates 2,777 events, ALL sports (NCAAF, NCAAM/W, NHL, NBA, NFL, tennis, UFC); 0 of the 1,406 collections include any Politics series event. Mentions parlays (13) are speech-word legs. Counts of parlay markets settled not pulled (need /markets by KXMVE series; next step). Politics legs must be built by us (simulation) since Kalshi lists none.
Method: GET /series?category=Politics&include_volume=true gives 2,458 series (1,961 with volume, total 1.396 billion contracts). Per-series GET /markets (limit 1000, all statuses) pulled for the top series by lifetime volume, in volume order: 226 series, 3257 markets, 2283 settled; covers 92.8% of volume. Pull continues in background (resumable, done.txt); rerun an.py to refresh.
Caveats: (1) no first-trade time without trades pulls, open_time to close_time is the stand-in (close_time may be the scheduled close, so early-closing markets look longer than they were); (2) spread = yes ask minus yes bid on currently open markets with both sides (blank if none open); (3) 170 of the 226 pulled series have 0 settled markets (long-dated one-offs: Fed chair, shutdown, DHS funding, cabinet). (4) Weekly series are only 8 to 12 events old, so almost nothing reaches 30 settled events.
Series tags: Congress 515, Trump 447, International 330, SCOTUS 179, Local 124; frequency one_off 1345, custom 976, annual 60, monthly 34, weekly 33, daily 9, hourly 1.
Series with >=30 settled events (step 2 calibration universe): KXTRUMPAPPROVE (68 events, 612 markets), KXVHGCB (41, 367). Overlap with w_cat_polent: check its cand.json; both are recurring with volume over 1,000 so likely both there.
TOP 10 BY SETTLED MARKETS
KXTRUMPAPPROVE 612 vol 18.75M ev 68 mk 612 sp 0.04 medd 1.124 f14 1.0 | Trump approval rating
KXVHGCB 367 vol 1.09M ev 41 mk 367 sp - medd 1.294 f14 1.0 | VoteHub GCB
KXTRUMPACT 107 vol 2.63M ev 10 mk 107 sp 0.01 medd 6.917 f14 1.0 | Will Trump do anything today?
KXHORMUZWEEKLY 106 vol 7.85M ev 10 mk 106 sp 0.01 medd 10.854 f14 1.0 | Traffic through the Strait of 
KXTRUTHSOCIAL 105 vol 7.97M ev 10 mk 105 sp 0.01 medd 6.999 f14 1.0 | Number of Trump Truth Social p
KXACTBLUETOP 78 vol 1.01M ev 12 mk 78 sp - medd 6.895 f14 1.0 | Top ActBlue fundraiser?
KXBABELMANDEBWEEKLY 77 vol 1.30M ev 10 mk 77 sp 0.01 medd 10.875 f14 1.0 | Traffic through the Bab el-Man
KXHORMUZPEAK 75 vol 1.34M ev 11 mk 75 sp 0.01 medd 10.833 f14 1.0 | Peak traffic through the Strai
KXTRUMPENDORSEMENTS 74 vol 1.12M ev 10 mk 74 sp 0.02 medd 6.0 f14 1.0 | How many people will Trump end
KXAPRPOTUS 72 vol 10.23M ev 9 mk 72 sp 0.01 medd 6.958 f14 1.0 | President RCP approval rating 
TOP 10 SETTLING WITHIN 14 DAYS (count; owner rule: max hold 14d)
KXTRUMPAPPROVE 612 vol 18.75M ev 68 mk 612 sp 0.04 medd 1.124 f14 1.0 | Trump approval rating
KXVHGCB 367 vol 1.09M ev 41 mk 367 sp - medd 1.294 f14 1.0 | VoteHub GCB
KXTRUMPACT 107 vol 2.63M ev 10 mk 107 sp 0.01 medd 6.917 f14 1.0 | Will Trump do anything today?
KXHORMUZWEEKLY 106 vol 7.85M ev 10 mk 106 sp 0.01 medd 10.854 f14 1.0 | Traffic through the Strait of 
KXTRUTHSOCIAL 105 vol 7.97M ev 10 mk 105 sp 0.01 medd 6.999 f14 1.0 | Number of Trump Truth Social p
KXACTBLUETOP 78 vol 1.01M ev 12 mk 78 sp - medd 6.895 f14 1.0 | Top ActBlue fundraiser?
KXBABELMANDEBWEEKLY 77 vol 1.30M ev 10 mk 77 sp 0.01 medd 10.875 f14 1.0 | Traffic through the Bab el-Man
KXHORMUZPEAK 75 vol 1.34M ev 11 mk 75 sp 0.01 medd 10.833 f14 1.0 | Peak traffic through the Strai
KXTRUMPENDORSEMENTS 74 vol 1.12M ev 10 mk 74 sp 0.02 medd 6.0 f14 1.0 | How many people will Trump end
KXAPRPOTUS 72 vol 10.23M ev 9 mk 72 sp 0.01 medd 6.958 f14 1.0 | President RCP approval rating 
SCHEDULED-EVENT / DEADLINE series by volume (all, mostly long dated)
KXGOVSHUTLENGTH 120044322.00 vol 120.04M ev 0 mk 0 sp - medd - f14 - | Number of days of government s
KXGOVSHUT 68855964.00 vol 68.86M ev 0 mk 0 sp - medd - f14 - | Government shutdown
KXHORMUZNORM 48764150.00 vol 48.76M ev 1 mk 2 sp 0.01 medd 161.666 f14 0.0 | When will traffic at the Strai
KXGOVTSHUTLENGTH 22717749.00 vol 22.72M ev 0 mk 0 sp 0.08 medd - f14 - | How long will the next governm
KXTRUMPAPPROVE 18748071.00 vol 18.75M ev 68 mk 612 sp 0.04 medd 1.124 f14 1.0 | Trump approval rating
KXDHSFUND 18502610.00 vol 18.50M ev 0 mk 0 sp - medd - f14 - | When will Congress fund DHS ag
KXCABOUT 16032631.00 vol 16.03M ev 1 mk 25 sp 0.098 medd 168.042 f14 0.0 | Next Cabinet memeber out
TOP 20 BY VOLUME (contracts)
KXFEDCHAIRNOM 216970762.00 vol 216.97M ev 0 mk 0 sp - medd - f14 - | Fed Chair nominee
KXGOVSHUTLENGTH 120044322.00 vol 120.04M ev 0 mk 0 sp - medd - f14 - | Number of days of government s
KXGOVSHUT 68855964.00 vol 68.86M ev 0 mk 0 sp - medd - f14 - | Government shutdown
KXHORMUZNORM 48764150.00 vol 48.76M ev 1 mk 2 sp 0.01 medd 161.666 f14 0.0 | When will traffic at the Strai
KXGOVTSHUTDOWN 31129485.00 vol 31.13M ev 1 mk 1 sp 0.01 medd 113.713 f14 0.0 | Will the government shut down?
KXUSAIRANAGREEMENT 24404800.00 vol 24.40M ev 1 mk 2 sp 0.015 medd 148.471 f14 0.0 | US Iran nuclear deal
KXGOVTSHUTLENGTH 22717749.00 vol 22.72M ev 0 mk 0 sp 0.08 medd - f14 - | How long will the next governm
KXTRUMPAPPROVE 18748071.00 vol 18.75M ev 68 mk 612 sp 0.04 medd 1.124 f14 1.0 | Trump approval rating
KXDHSFUND 18502610.00 vol 18.50M ev 0 mk 0 sp - medd - f14 - | When will Congress fund DHS ag
KXNOBELPEACE 17701842.00 vol 17.70M ev 1 mk 50 sp 0.007 medd 14.609 f14 0.26 | Nobel Peace Prize
KXTRUMPUFC 16388541.00 vol 16.39M ev 3 mk 3 sp 0.025 medd 61.917 f14 0.0 | Trump attend another UFC event
KXSAVEACT 16058426.00 vol 16.06M ev 0 mk 0 sp 0.004 medd - f14 - | Will the SAVE Act become law?
KXCABOUT 16032631.00 vol 16.03M ev 1 mk 25 sp 0.098 medd 168.042 f14 0.0 | Next Cabinet memeber out
KXATTENDSOTU 15535513.00 vol 15.54M ev 0 mk 0 sp - medd - f14 - | Who will attend the State of t
KXEOWEEK 14391621.00 vol 14.39M ev 8 mk 30 sp 0.04 medd 13.048 f14 0.633 | EO this week?
KXTRUMPADMINLEAVE 13477522.00 vol 13.48M ev 1 mk 3 sp 0.05 medd 325.541 f14 0.0 | Who will leave the Trump admin
KXTRUMPOUT27 12945358.00 vol 12.95M ev 0 mk 0 sp 0.01 medd - f14 - | Trump out as President?
KXSECAG 12672827.00 vol 12.67M ev 0 mk 0 sp - medd - f14 - | Next Attorney General
KXNEXTPRESSECPERM 12561137.00 vol 12.56M ev 0 mk 0 sp 0.01 medd - f14 - | Next permanent White House Pre
KXSECDEF 12475893.00 vol 12.48M ev 0 mk 0 sp - medd - f14 - | New Secretary of Defense
LATER-ONLY (no settled market yet; settle past 14 days or still open): KXFEDCHAIRNOM, KXGOVSHUTLENGTH, KXGOVSHUT, KXGOVTSHUTLENGTH, KXDHSFUND, KXSAVEACT, KXATTENDSOTU, KXTRUMPOUT27, KXSECAG, KXNEXTPRESSECPERM, KXSECDEF, KXSECHHS, KXNEXTAG, KXBIDENPARDON, KXTRUMPATTEND, KXTRUMPPARDON, KXLEAVEPOWELL, KXTRUMPOUT, KXFEDCHAIRCONFIRM, KXIMPEACH, KXGREENLAND, KXPRESNOMFEDCHAIR, KXMJSCHEDULE, KXCLOSEHORMUZ, KXGOLDCARDS
