# NBA-fantasy-app

## Opis

Aplikacija je namenjena igranju NBA fantasy league-a. Uporabnik se ob prvi uporabi registrira, izbere ekipo igralcev, ki mu na podlagi resnične statistike odigranih tekem v NBA prinašajo točke. Te igralci dobijo na podlagi svojega uspeha v "resničnih" tekmah - več točk, asistenc, blokov itd. pomeni boljši rezultat, v primeru slabe igre pa lahko igralec dobi tudi negativne točke.

 Cilj vsakega uporabnika aplikacije je, da zbere čim več točk. 

Statistične podatke o tekmah in igralcih sva pridobila s spletnih strani [basketball-reference.com](basketball-reference.com) in [NatStat.com](https://natstat.com/).

### ER diagram

Povezava do [ER](https://github.com/marci314/NBA-fantasy-app/blob/main/Presentation/static/Images/opber3.png) diagrama.

### Struktura baze

Seznam tabel, ki jih imava v naši bazi:

- **uporabnik** (uporabnik_id, uporabnisko_ime, geslo, last_login)
- **fantasy_ekipa** (f_ekipa_id, tocke, lastnik, ime_ekipe)
- **igralec** (igralec_id, ime, pozicija, visina, rojstvo)
- **trener** (trener_id, ime, rojstvo)
- **fantasy_ekipa_trener** (f_ekipa_id, trener_id)
- **ekipa** (ekipa_id, ekipa_ime)
- **tekma** (id_tekma, domaca_ekipa, gostujoca_ekipa, domaca_ekipa_tocke, gostujoca_ekipa_tocke, datum)
- **podatki_o_tekmi** (id_igralca, id_tekme, odstotek_meta, ukradene, bloki, izgubljene, skoki, podaje, odigrane_minute, tocke, izid)
- **fantasy_ekipa_igralci** (f_ekipa_id, igralec_id)
- **igralci_tocke** (id_igralca, id_tekme, tocke)
- **igralci_ekipe** (id_igralca, id_ekipa)
- **trenerji_ekipe** (trener_id, ekipa_id)

## Navodila za uporabo aplikacije

1. **Registracija:** Po zagonu aplikacije se registrirajte z uporabniškim imenom, geslom in poimenujte svojo fantasy ekipo.
2. **Prijava:** Prijavite se z vašim uporabniškim imenom in geslom.
3. **Preberite pravila:** Pojdite na zavihek "Pravila" in si preberite osnovna pravila in potek igre.
4. **Izbira igralcev in trenerja:** Vsak uporabnik lahko v svojo ekipo izbere največ 5 igralcev in enega trenerja. Predhodno si lahko ogledate ekipe drugih uporabnikov ter spored tekem in se na podlagi tega odločite o svoji izbiri.
5. **Izberite časovno okno:** V zavihku "Simuliraj tekme" določite časovno okno, v katerem želite simulirat tekme.
6. **Pregled rezultatov:** Po odigranih tekmah si v zavihku "Poglej lestvico" lahko ogledate uvrstitev vaše fantasy ekipe.

#### Spletni dostop

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/marci314/NBA-fantasy-app.git/main?urlpath=proxy/8081/)



















