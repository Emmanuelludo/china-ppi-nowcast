# Additional product PPI forecasts

Target: 2026-09; as of 2026-09-24T15:48:21.691812+08:00

Existing models remain active. These additional candidates do not replace them.
20th-to-20th waits for the current 11–20 release; it is a period-price proxy.

|Timing|Panel|Model|MoM (%)|
|---|---|---|---:|
|twentieth|union|ridge|-0.342|
|twentieth|union|histgb|+0.691|
|twentieth|union|xgboost|+0.682|
|twentieth|union|catboost|+0.729|
|twentieth|union|lightgbm|+0.644|
|twentieth|union|category_factor|+0.949|
|twentieth|union|sector_first|+1.261|
|twentieth|union|random_forest|+0.614|
|twentieth|union|economic_ml_hybrid|+0.945|
|twentieth|union|direct_tracker|+6.123|
|twentieth|stable|ridge|+0.814|
|twentieth|stable|histgb|+0.697|
|twentieth|stable|xgboost|+0.652|
|twentieth|stable|catboost|+0.802|
|twentieth|stable|lightgbm|+0.719|
|final|union|ridge|+1.218|
|final|union|histgb|+0.744|
|final|union|xgboost|+0.696|
|final|union|catboost|+0.639|
|final|union|lightgbm|+0.671|
|early|union|ridge|+0.913|
|early|union|histgb|+0.596|
|early|union|xgboost|+0.618|
|early|union|catboost|+0.471|
|early|union|lightgbm|+0.561|
|early_carry|union|ridge|+1.207|
|early_carry|union|histgb|+0.677|
|early_carry|union|xgboost|+0.675|
|early_carry|union|catboost|+0.605|
|early_carry|union|lightgbm|+0.669|

Direct tracker is uncalibrated. No ensemble weights or model winner have been promoted.
Individual and grouped SHAP files are stored beside each tree forecast. They are model attributions, not causal contributions.
Verified historical source range: 2014-01-01–2026-09-10. See the historical discovery audit for gaps.

## twentieth / histgb attribution

Baseline: +0.0301 pp; prediction: +0.6909%.

|Product feature|SHAP (pp)|
|---|---:|
|price: 液化石油气(LPG)|+0.2133|
|price: 甲醇(优等品)|+0.1787|
|price: 山西大混(5000大卡)|+0.0875|
|price: 大同混煤(5800大卡)|+0.0761|
|price: 顺丁胶(BR9000)|+0.0730|
|price: 纯苯(石油苯,工业级)|+0.0505|
|price: 农药(草甘膦,95%原药)|-0.0471|
|price: 硫酸(98%)|-0.0451|

|Group|SHAP (pp)|
|---|---:|
|石油天然气|+0.2731|
|化工产品|+0.2665|
|煤炭|+0.1908|
|农业生产资料|-0.0714|
|非金属矿物制品|+0.0251|
|农产品（主要用于加工）|-0.0178|
|黑色金属|-0.0125|
|有色金属|+0.0037|
|林产品|+0.0021|
|非金属建材|+0.0012|

## twentieth / xgboost attribution

Baseline: +0.0241 pp; prediction: +0.6820%.

|Product feature|SHAP (pp)|
|---|---:|
|price: 液化石油气(LPG)|+0.2468|
|price: 甲醇(优等品)|+0.1371|
|price: 大同混煤(5800大卡)|+0.0810|
|price: 硫酸(98%)|-0.0762|
|price: 山西大混(5000大卡)|+0.0687|
|price: 顺丁胶(BR9000)|+0.0572|
|price: 纯苯(石油苯,工业级)|+0.0463|
|price: 普通混煤(4500大卡)|+0.0363|

|Group|SHAP (pp)|
|---|---:|
|石油天然气|+0.3148|
|煤炭|+0.2048|
|化工产品|+0.1475|
|农业生产资料|-0.0614|
|黑色金属|+0.0469|
|非金属矿物制品|+0.0338|
|农产品（主要用于加工）|-0.0294|
|有色金属|-0.0056|
|非金属建材|+0.0040|
|林产品|+0.0025|

## twentieth / catboost attribution

Baseline: +0.0253 pp; prediction: +0.7288%.

|Product feature|SHAP (pp)|
|---|---:|
|price: 甲醇(优等品)|+0.3858|
|price: 液化石油气(LPG)|+0.1943|
|price: 硫酸(98%)|-0.0727|
|price: 聚丙烯(拉丝料)|+0.0599|
|price: 柴油(0#国VI)|+0.0458|
|price: 顺丁胶(BR9000)|+0.0383|
|price: 纯苯(石油苯,工业级)|+0.0331|
|price: 山西优混(5500大卡)|+0.0316|

|Group|SHAP (pp)|
|---|---:|
|化工产品|+0.4269|
|石油天然气|+0.2543|
|农业生产资料|-0.0357|
|非金属矿物制品|+0.0192|
|有色金属|+0.0140|
|农产品（主要用于加工）|+0.0114|
|黑色金属|+0.0109|
|煤炭|+0.0025|
|非金属建材|+0.0000|
|林产品|-0.0000|

## twentieth / lightgbm attribution

Baseline: +0.0306 pp; prediction: +0.6445%.

|Product feature|SHAP (pp)|
|---|---:|
|price: 液化石油气(LPG)|+0.1843|
|price: 甲醇(优等品)|+0.0942|
|price: 大同混煤(5800大卡)|+0.0846|
|price: 硫酸(98%)|-0.0686|
|price: 普通混煤(4500大卡)|+0.0564|
|price: 顺丁胶(BR9000)|+0.0557|
|price: 纯苯(石油苯,工业级)|+0.0381|
|price: 普通中板(20mm,Q235)|+0.0378|

|Group|SHAP (pp)|
|---|---:|
|石油天然气|+0.2640|
|煤炭|+0.1789|
|化工产品|+0.1345|
|黑色金属|+0.0418|
|非金属矿物制品|+0.0286|
|农产品（主要用于加工）|-0.0251|
|有色金属|-0.0131|
|非金属建材|+0.0044|
|农业生产资料|-0.0033|
|林产品|+0.0032|

## twentieth / random_forest attribution

Baseline: +0.0382 pp; prediction: +0.6145%.

|Product feature|SHAP (pp)|
|---|---:|
|price: 液化石油气(LPG)|+0.1862|
|price: 甲醇(优等品)|+0.1816|
|price: 纯苯(石油苯,工业级)|+0.0552|
|price: 无缝钢管(219*6,20#)|-0.0355|
|price: 大同混煤(5800大卡)|+0.0341|
|price: 液化天然气(LNG)|+0.0230|
|price: 聚丙烯(拉丝料)|+0.0225|
|price: 山西大混(5000大卡)|+0.0220|

|Group|SHAP (pp)|
|---|---:|
|化工产品|+0.2716|
|石油天然气|+0.2282|
|煤炭|+0.0721|
|黑色金属|-0.0251|
|有色金属|+0.0163|
|非金属建材|+0.0130|
|农产品（主要用于加工）|-0.0058|
|非金属矿物制品|+0.0039|
|林产品|+0.0025|
|农业生产资料|-0.0006|

## final / histgb attribution

Baseline: +0.0153 pp; prediction: +0.7439%.

|Product feature|SHAP (pp)|
|---|---:|
|price: 甲醇(优等品)|+0.1960|
|price: 无缝钢管(219*6,20#)|+0.1344|
|price: 液化石油气(LPG)|+0.1295|
|price: 汽油(95#国VI)|+0.0731|
|price: 农药(草甘膦,95%原药)|-0.0723|
|price: 聚氯乙烯(SG5)|+0.0722|
|price: 大同混煤(5800大卡)|+0.0495|
|price: 柴油(0#国VI)|+0.0490|

|Group|SHAP (pp)|
|---|---:|
|化工产品|+0.3122|
|石油天然气|+0.2632|
|黑色金属|+0.1359|
|煤炭|+0.1007|
|农业生产资料|-0.0963|
|非金属建材|+0.0140|
|农产品（主要用于加工）|-0.0128|
|林产品|+0.0049|
|非金属矿物制品|+0.0047|
|有色金属|+0.0022|

## final / xgboost attribution

Baseline: +0.0155 pp; prediction: +0.6962%.

|Product feature|SHAP (pp)|
|---|---:|
|price: 液化石油气(LPG)|+0.1607|
|price: 甲醇(优等品)|+0.1537|
|price: 无缝钢管(219*6,20#)|+0.1250|
|price: 柴油(0#国VI)|+0.0790|
|price: 农药(草甘膦,95%原药)|-0.0572|
|price: 山西大混(5000大卡)|+0.0561|
|price: 大同混煤(5800大卡)|+0.0528|
|price: 普通混煤(4500大卡)|+0.0392|

|Group|SHAP (pp)|
|---|---:|
|石油天然气|+0.2651|
|化工产品|+0.1724|
|煤炭|+0.1598|
|黑色金属|+0.1276|
|农业生产资料|-0.0818|
|有色金属|+0.0253|
|非金属矿物制品|+0.0196|
|农产品（主要用于加工）|-0.0123|
|非金属建材|+0.0062|
|林产品|-0.0012|

## final / catboost attribution

Baseline: +0.0143 pp; prediction: +0.6389%.

|Product feature|SHAP (pp)|
|---|---:|
|price: 甲醇(优等品)|+0.2884|
|price: 液化石油气(LPG)|+0.1148|
|price: 无缝钢管(219*6,20#)|+0.1005|
|price: 汽油(95#国VI)|+0.0641|
|price: 柴油(0#国VI)|+0.0454|
|price: 纯苯(石油苯,工业级)|+0.0346|
|price: 农药(草甘膦,95%原药)|-0.0326|
|price: 热轧普通薄板(3mm,Q235)|-0.0314|

|Group|SHAP (pp)|
|---|---:|
|化工产品|+0.3266|
|石油天然气|+0.2357|
|黑色金属|+0.0653|
|农业生产资料|-0.0411|
|农产品（主要用于加工）|+0.0229|
|有色金属|+0.0181|
|林产品|-0.0083|
|煤炭|+0.0039|
|非金属矿物制品|+0.0008|
|非金属建材|+0.0006|

## final / lightgbm attribution

Baseline: +0.0159 pp; prediction: +0.6706%.

|Product feature|SHAP (pp)|
|---|---:|
|price: 液化石油气(LPG)|+0.1395|
|price: 甲醇(优等品)|+0.1317|
|price: 无缝钢管(219*6,20#)|+0.1127|
|price: 柴油(0#国VI)|+0.0960|
|price: 大同混煤(5800大卡)|+0.0548|
|price: 农药(草甘膦,95%原药)|-0.0501|
|price: 硫酸(98%)|-0.0464|
|price: 角钢(5#)|+0.0419|

|Group|SHAP (pp)|
|---|---:|
|石油天然气|+0.2592|
|化工产品|+0.1810|
|黑色金属|+0.1450|
|煤炭|+0.1228|
|农业生产资料|-0.0854|
|非金属建材|+0.0155|
|有色金属|+0.0129|
|非金属矿物制品|+0.0108|
|农产品（主要用于加工）|-0.0036|
|林产品|-0.0033|

## early / histgb attribution

Baseline: +0.0303 pp; prediction: +0.5959%.

|Product feature|SHAP (pp)|
|---|---:|
|price: 甲醇(优等品)|+0.1719|
|price: 聚氯乙烯(SG5)|+0.1269|
|price: 汽油(95#国VI)|+0.0703|
|price: 柴油(0#国VI)|+0.0573|
|price: 农药(草甘膦,95%原药)|-0.0558|
|price: 纯苯(石油苯,工业级)|+0.0428|
|price: 角钢(5#)|+0.0418|
|price: 液化石油气(LPG)|+0.0352|

|Group|SHAP (pp)|
|---|---:|
|化工产品|+0.3451|
|石油天然气|+0.1862|
|农业生产资料|-0.0906|
|煤炭|+0.0418|
|黑色金属|+0.0314|
|非金属矿物制品|+0.0173|
|农产品（主要用于加工）|+0.0158|
|非金属建材|+0.0109|
|有色金属|+0.0085|
|林产品|-0.0007|

## early / xgboost attribution

Baseline: +0.0245 pp; prediction: +0.6180%.

|Product feature|SHAP (pp)|
|---|---:|
|price: 甲醇(优等品)|+0.1488|
|price: 聚氯乙烯(SG5)|+0.0838|
|price: 汽油(95#国VI)|+0.0741|
|price: 农药(草甘膦,95%原药)|-0.0617|
|price: 纯苯(石油苯,工业级)|+0.0551|
|price: 柴油(0#国VI)|+0.0490|
|price: 液化石油气(LPG)|+0.0405|
|price: 无缝钢管(219*6,20#)|+0.0391|

|Group|SHAP (pp)|
|---|---:|
|化工产品|+0.3024|
|石油天然气|+0.1874|
|农业生产资料|-0.0864|
|煤炭|+0.0705|
|黑色金属|+0.0525|
|非金属矿物制品|+0.0288|
|农产品（主要用于加工）|+0.0270|
|非金属建材|+0.0126|
|林产品|-0.0095|
|有色金属|+0.0080|

## early / catboost attribution

Baseline: +0.0294 pp; prediction: +0.4710%.

|Product feature|SHAP (pp)|
|---|---:|
|price: 甲醇(优等品)|+0.1774|
|price: 柴油(0#国VI)|+0.0783|
|price: 纯苯(石油苯,工业级)|+0.0649|
|price: 汽油(95#国VI)|+0.0561|
|price: 无缝钢管(219*6,20#)|+0.0519|
|price: 农药(草甘膦,95%原药)|-0.0491|
|price: 液化石油气(LPG)|+0.0370|
|price: 普通中板(20mm,Q235)|+0.0329|

|Group|SHAP (pp)|
|---|---:|
|化工产品|+0.2270|
|石油天然气|+0.1756|
|农业生产资料|-0.0662|
|黑色金属|+0.0562|
|农产品（主要用于加工）|+0.0203|
|有色金属|+0.0188|
|非金属建材|+0.0081|
|非金属矿物制品|+0.0029|
|煤炭|-0.0017|
|林产品|+0.0003|

## early / lightgbm attribution

Baseline: +0.0292 pp; prediction: +0.5612%.

|Product feature|SHAP (pp)|
|---|---:|
|price: 甲醇(优等品)|+0.1573|
|price: 聚氯乙烯(SG5)|+0.0786|
|price: 纯苯(石油苯,工业级)|+0.0723|
|price: 农药(草甘膦,95%原药)|-0.0694|
|price: 柴油(0#国VI)|+0.0536|
|price: 无缝钢管(219*6,20#)|+0.0512|
|price: 液化石油气(LPG)|+0.0506|
|price: 复合肥(硫酸钾复合肥,氮磷钾含量45%)|-0.0354|

|Group|SHAP (pp)|
|---|---:|
|化工产品|+0.2964|
|石油天然气|+0.1537|
|农业生产资料|-0.1103|
|煤炭|+0.0686|
|黑色金属|+0.0649|
|农产品（主要用于加工）|+0.0226|
|非金属矿物制品|+0.0191|
|有色金属|+0.0156|
|非金属建材|+0.0049|
|林产品|-0.0035|

## early_carry / histgb attribution

Baseline: +0.0280 pp; prediction: +0.6769%.

|Product feature|SHAP (pp)|
|---|---:|
|price: 甲醇(优等品)|+0.1673|
|price: 汽油(95#国VI)|+0.1651|
|price: 角钢(5#)|+0.0652|
|price: 无缝钢管(219*6,20#)|+0.0590|
|price: 纯苯(石油苯,工业级)|+0.0545|
|carry: 普通混煤(4500大卡)|+0.0529|
|price: 柴油(0#国VI)|+0.0518|
|carry: 农药(草甘膦,95%原药)|-0.0365|

|Group|SHAP (pp)|
|---|---:|
|石油天然气|+0.2623|
|化工产品|+0.2268|
|煤炭|+0.0910|
|农业生产资料|-0.0893|
|黑色金属|+0.0886|
|农产品（主要用于加工）|+0.0360|
|非金属矿物制品|+0.0128|
|林产品|+0.0128|
|非金属建材|+0.0098|
|有色金属|-0.0021|

## early_carry / xgboost attribution

Baseline: +0.0232 pp; prediction: +0.6750%.

|Product feature|SHAP (pp)|
|---|---:|
|price: 甲醇(优等品)|+0.1545|
|price: 汽油(95#国VI)|+0.1263|
|price: 柴油(0#国VI)|+0.0705|
|price: 纯苯(石油苯,工业级)|+0.0625|
|price: 无缝钢管(219*6,20#)|+0.0582|
|price: 聚氯乙烯(SG5)|+0.0405|
|price: 角钢(5#)|+0.0403|
|price: 大同混煤(5800大卡)|+0.0330|

|Group|SHAP (pp)|
|---|---:|
|化工产品|+0.2577|
|石油天然气|+0.2481|
|煤炭|+0.0968|
|农业生产资料|-0.0897|
|黑色金属|+0.0851|
|农产品（主要用于加工）|+0.0304|
|有色金属|+0.0182|
|非金属矿物制品|+0.0130|
|林产品|-0.0116|
|非金属建材|+0.0040|

## early_carry / catboost attribution

Baseline: +0.0265 pp; prediction: +0.6052%.

|Product feature|SHAP (pp)|
|---|---:|
|price: 甲醇(优等品)|+0.1942|
|price: 汽油(95#国VI)|+0.1509|
|price: 无缝钢管(219*6,20#)|+0.0601|
|price: 纯苯(石油苯,工业级)|+0.0584|
|price: 液化石油气(LPG)|+0.0470|
|price: 柴油(0#国VI)|+0.0370|
|carry: 液化石油气(LPG)|+0.0295|
|price: 农药(草甘膦,95%原药)|-0.0239|

|Group|SHAP (pp)|
|---|---:|
|石油天然气|+0.2819|
|化工产品|+0.2509|
|农业生产资料|-0.0610|
|黑色金属|+0.0512|
|农产品（主要用于加工）|+0.0192|
|有色金属|+0.0159|
|非金属矿物制品|+0.0094|
|煤炭|+0.0089|
|非金属建材|+0.0031|
|林产品|-0.0008|

## early_carry / lightgbm attribution

Baseline: +0.0276 pp; prediction: +0.6691%.

|Product feature|SHAP (pp)|
|---|---:|
|price: 甲醇(优等品)|+0.1673|
|price: 汽油(95#国VI)|+0.1092|
|price: 柴油(0#国VI)|+0.0833|
|price: 无缝钢管(219*6,20#)|+0.0618|
|price: 纯苯(石油苯,工业级)|+0.0609|
|carry: 农药(草甘膦,95%原药)|-0.0426|
|price: 大同混煤(5800大卡)|+0.0405|
|price: 农药(草甘膦,95%原药)|-0.0326|

|Group|SHAP (pp)|
|---|---:|
|石油天然气|+0.2748|
|化工产品|+0.2566|
|农业生产资料|-0.1088|
|煤炭|+0.1069|
|黑色金属|+0.0428|
|农产品（主要用于加工）|+0.0376|
|非金属矿物制品|+0.0181|
|有色金属|+0.0087|
|非金属建材|+0.0037|
|林产品|+0.0011|
