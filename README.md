# 3D-pi-scanner
3D pi-scanner koristi Raspberry pi sa shieldom za 4 kamere, sto će se napraviti s BJY28 i 3d print nova verzija starog RT360, 

//triger() je viška, nije se uspio osposobiti sip1A05 kako bi trigao vanski trigger od fotoaparata.
//skech se sastoji od 7 programa odmah tu dolje piše. nedostaje 7.isto kao i 6. program samo arduino daje znak raspberriju kad da slika i razberi daje povratno arduinu status
//to se odvija preko seriske komunikacije USB. Bluetooth ili bolje BLE je bio pre kompliciran za izvesti u odnosu na USB.
//7.1 program koji ima isto kao i 6. program korake od 5° ali pojedinačno treba
//za svako slikanje stiskati start (to je namjenjeno za slikanje dna predmeta). Postoje 3 tipke Start Stop i Program, ne treba obajšnjavati što koja radi
//međutim ono što nedostaje je kombinacija tipki Program+Start kako bi se aktivirao 7.1 program ili ako ćemo pojednostavniti dodajmo 8. program.
//Jedna kombinacija tipti ili dugo držanje stop tipke bila bi dobra za posebnu funkciju "brisanje fotografija u folderu na RPI kako bi krenuli iznova.
//RPI 5 ima instaliran Wormbook i ima genue remote preko htmla tako da je jednostavno se spojiti na RPI bilo čime.

Rpi softwer mora biti napravljen u pythonu i flsku.
za sad jednostavna komunikacija između arduina i raspberija. arduino da znak RPI da može fotkati, Rpi fotka i daje status da je gotov s slikanjem te arduino okreće stol.
RT360 ima 2 pi camere V3 sa auto focusom tako da će to biti izazov fokusirati obje kamere odjednom.
Treba proučiti picamera2 dokumentaciju 
https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf

CAD model
https://cad.onshape.com/documents/63ecde2190418fba67f2fb9b/w/8bdd8ba014811db917c3541b/e/cbe620df5bb5ad7eb854756c

[Foto tent](https://vi.aliexpress.com/item/1005003505429319.html?spm=a2g0o.detail.pcDetailTopMoreOtherSeller.3.49e64n2j4n2js5&gps-id=pcDetailTopMoreOtherSeller&scm=1007.40000.327270.0&scm_id=1007.40000.327270.0&scm-url=1007.40000.327270.0&pvid=6ccd668d-0e58-4e03-be44-67a425d32d8d&_t=gps-id:pcDetailTopMoreOtherSeller,scm-url:1007.40000.327270.0,pvid:6ccd668d-0e58-4e03-be44-67a425d32d8d,tpp_buckets:668%232846%238116%232002&pdp_npi=4%40dis%21EUR%2160.44%2135.06%21%21%2160.44%2135.06%21%40211b876717273869961245081e9477%2112000036979653322%21rec%21HR%212778110335%21XZ&utparam-url=scene%3ApcDetailTopMoreOtherSeller%7Cquery_from%3A)

[Rpi 4 kamera shied](https://www.arducam.com/multi-camera-adapter-module-raspberry-pi/)

