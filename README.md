#RT360 raspberry pi scanner
RT360 je 3D scanner koristi Raspberry pi s dvije V3 Pi kamere, s 28BJY-48 i 3d print nova verzija starog RT360, 

Skener je napravljem s glavnom funkcijom fotogramtrije, Flask app upravlja preko serijske komunikacije između Raspberry pi i Arduina.
Sam arduino ima 6 programa za ručno fotografiranje ili snimanje, to je kao nadogradnja za buduće korištenje zajedno sa trigerom za vanjski fotoaparat.

Program br 6 namjenjen je za fotogrametriju i po defaultu je prvi izabran prilikom paljenja arduina. Pomiče stol za otprilike 5° i fotografira 72 puta za jedan kruga,
te pojedinačno treba za svako slikanje stiskati start (to je namjenjeno za slikanje dna predmeta). Postoje 3 tipke Start Stop i Program, ne treba obajšnjavati što koja radi.

RPI 5 ima instaliran Wormbook OS i ima genue remote preko htmla tako da je jednostavno se spojiti na Raspberry Pi.
Rpi softwer napravljen je u pythonu/flsku.
Sučelje je dosta jednostavno napravljeno za upravljanje skenerom, Start Stop tipke, novi folder, pojedinačno fotografiranje (za dno predmeta), pokretanje live feeda i zaustavljanje,
autofocus i starnica za pomoć gdje je sve objašnjeno.

RT360 ima 2 pi camere V3 sa auto focusom.

picamera2 [dokumentacija](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf)

[CAD model](https://cad.onshape.com/documents/63ecde2190418fba67f2fb9b/w/8bdd8ba014811db917c3541b/e/cbe620df5bb5ad7eb854756c)

[Foto tent](https://vi.aliexpress.com/item/1005003505429319.html?spm=a2g0o.detail.pcDetailTopMoreOtherSeller.3.49e64n2j4n2js5&gps-id=pcDetailTopMoreOtherSeller&scm=1007.40000.327270.0&scm_id=1007.40000.327270.0&scm-url=1007.40000.327270.0&pvid=6ccd668d-0e58-4e03-be44-67a425d32d8d&_t=gps-id:pcDetailTopMoreOtherSeller,scm-url:1007.40000.327270.0,pvid:6ccd668d-0e58-4e03-be44-67a425d32d8d,tpp_buckets:668%232846%238116%232002&pdp_npi=4%40dis%21EUR%2160.44%2135.06%21%21%2160.44%2135.06%21%40211b876717273869961245081e9477%2112000036979653322%21rec%21HR%212778110335%21XZ&utparam-url=scene%3ApcDetailTopMoreOtherSeller%7Cquery_from%3A)

RT360 trebao je imati 4 kamere ali zbog praktičnoti i opcije da RPI 5 ima dva BUS conektora za kamere, napravljen je s 2 kamere koje kližu po nosaču.
Novija verzija (ako bude) neće imati Arduino jer RPI može samostalno upravljati stepper motorom što bi pojednostavnilo izvedbu i upravljanje.
[Rpi 4 kamera shied](https://www.arducam.com/multi-camera-adapter-module-raspberry-pi/)

