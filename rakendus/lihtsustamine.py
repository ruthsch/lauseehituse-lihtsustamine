#!/usr/bin/env python
# -*- coding: utf-8 -*-

#tekstidega tegelemiseks:

#veebis nltk kasutamiseks:
#import nltk
#nltk.data.path.append("/home/veebid/lihtlauseks/nltk_data")

#EstNLTK teegi abil tekstitöötluseks:
from estnltk import Text
from estnltk import synthesize 
import re

#käsurealt väljakutsumiseks:
from sys import argv
from html.parser import HTMLParser

#meetod 'uuenda_lause' loob String-tüüpi sisendi alusel uue Text-objekti
def uuenda_lause(lause):
    uus = Text(lause)
    uus.analysis
    return uus

#meetod 'tuvasta_alus' otsib verbi 'analysis' alusel kindlat tegijat ehk alust
def tuvasta_alus(verb):
#[{'root': 'hüppa', 'root_tokens': ['hüppa'], 'partofspeech': 'V', 'clitic': '', 'ending': 's', 'form': 's', 'lemma': 'hüppama'}]
    #pronoomenid ning neile 100% kuuluvad verbilõpud
    valikud = [('mina', ['n', 'nuksin', 'sin']), ('sina', ['d', 'o']), ('tema', ['b', 's']), \
               ('meie', ['me', 'neg me', 'nuksime', 'sime']), ('teie', ['te', 'neg ge', 'nuksite', 'site']), ('nemad', ['vad'])]
    
    #antud verbi lõpp
    l6pp = verb[0]['form']
    
    vastus = None
    #kontrollib iga lõppude listi
    for pronoomen, l6pud in valikud:
        #küsitud verbi lõpu abil saab määrata aluse -> lisatakse see alus vastuseks
        if l6pp in l6pud:  
            vastus = pronoomen
            break #kui vastus on leitud, võib tsükli lõpetada
               
    return vastus

#meetod 'sg_pl' otsib ette antud pronoomenile arvukategooria väärtust, sisseantud lause abil
def sg_pl(pronoomen, lause):
    lause = Text(lause)

    #leiab pronoomeni indeksi sõnede listis
    s6ned = lause.word_texts
    pr_indeks = s6ned.index(pronoomen)

    #enne seda on nimisõna/pärisnimi/pronoomen ja koma, siis võib selle vormi võtta
    if s6ned[pr_indeks-1]=="," and (lause.postags[pr_indeks-2] in ["S", "H", "P"]):
        vorm = lause.analysis[pr_indeks-2][0]['form'].split()[0] #vaja on ainult esimest osa (sg/pl)

    else: # muul juhul tagastada None
        vorm = None
        
    return vorm

#meetod 'tuvasta_subjekt' otsib (osa)lauses subjekti rollis olevatest sõnadest algses lauses objekti rollis olevat liiget
def tuvasta_subjekt(lause, algne):
    #lisab süntaksi kihi
    lause = Text(lause)
    lause.tag_syntax()
    
    algne = Text(algne)
    algne.tag_syntax()
    
    subjektid = []
    omadused = []
    subjektifraas = None
    
    #otsib osalausest subjektid ja eestäiendina esinevad adjektiivid
    lauseAnalyysid = list(zip(lause.word_texts, lause['conll_syntax']))
    for ls6na,lanalyys in lauseAnalyysid:
        if '@SUBJ' in lanalyys['parser_out'][0]:
            subjektid.append((ls6na, lanalyys['start'], lanalyys['end']))
        if '@AN>' in lanalyys['parser_out'][0]:
            omadused.append((ls6na, lanalyys['start'], lanalyys['end']))
    
    #kontrollib, kas mõni leitud subjektidest oleks algses lauses objekt
    if len(subjektid)!=0:
        algseAnalyysid = list(zip(algne.word_texts, algne['conll_syntax']))
        for s6na,analyys in algseAnalyysid:
            for subjekt in subjektid:
                if s6na==subjekt[0] and '@OBJ' in analyys['parser_out'][0]:
                    subjektifraas = subjekt
                    
                    #otsitab välja kogu fraasi
                    syntaksPuud = lause.syntax_trees()
                    # leiab subjektid ja nendele alluvad sõnad
                    s6ltuvad = syntaksPuud[0].as_dependencygraph()
                    kolmikud =  list(s6ltuvad.triples()) #listis, nt: (('naeratuse', 'S'), '@AN>', ('suure', 'A')),

                    for kolm in kolmikud: 
                        #kui on vastav subjekt/objekt ning selle juurde kuuluv adjektiiv
                        if (s6na in kolm[0]) and (kolm[1]=='@AN>'):
                            #leiab ja lisab õige omadussõna
                            for adj in omadused:
                                if kolm[2][0]==adj[0]:
                                    if adj[1]<subjektifraas[1]: #vajadusel muudab algkoordinaati
                                        subjektifraas = (kolm[2][0] +" "+ subjektifraas[0] , adj[1], subjektifraas[2])
                                    else:
                                        fraas = subjektifraas[0].split(" ", 1) #lahutab esimese tühiku kohalt
                                        subjektifraas = (fraas[0]+" "+kolm[2][0]+" "+fraas[1], subjektifraas[1], subjektifraas[2])
                    
                    return subjektifraas

    return None

#meetod 'lihtsusta' üritab moodustada ebakorrektsest ja elliptiliselt lausest mitte-elliptilist korrektset lauset
def lihtsusta(osalaused, pikk_lause):
    valjund_listina=[]
    
    eelmisest = None #vajadusel jäetakse meelde osa tekstist ja lisatakse järgmise lause algusesse
    o=0
    while o<len(osalaused):
        if osalaused[o]['text'] in [".", "!", "?", "***", "..."]: #antud juhud ei ole laused
            o+=1
            if o>=len(osalaused):
                break
        
        osalause=uuenda_lause(osalaused[o]) #salvestab hetkel uuritava osalause muutujasse
        if eelmisest: #vajadusel lisab eelmise osalause antud lause algusesse
            if osalause['words'][0]['analysis'][0]['partofspeech'] == 'Z': #kirjavahemärgi ette tühik ei käi
                osalause = uuenda_lause(eelmisest['text'] + osalause['text'])
            else: 
                osalause = uuenda_lause(eelmisest['text']+ ", " + osalause['text'])
            eelmisest = None
        
        #Muutused lause lõpuga seoses
        #kui osalause lõppeb sidesõnaga, mis ei ole 'või' ega 'ega', tuleb see kustutada
        if osalause['words'][-1]['analysis'][0]['partofspeech']=='J' and \
                osalause['words'][-1]['text'] not in ['või', 'ega']:
            viimase_sona_algus = osalause['words'][-1]['start']-1
            osalause=uuenda_lause(osalause['text'][:viimase_sona_algus])
        
        #vajadusel muudab/lisab lauselõpumärgi
        if osalause['words'][-1]['analysis'][0]['partofspeech']!='Z':
            if osalause['text'][-1]!='.':
                osalause = uuenda_lause(osalause['text']+".")
        elif osalause['words'][-1]['text'] in [',', ':', ';', ')', '-', '–']:
            osalause = uuenda_lause((osalause['text'][:-1]).strip()+".")
        
        #Muutused lause algusega seoses
        #kui osalause algab sidesõnaga (on 'ja' või 'ning' ega alga suurtähega), tuleb see välja jätta
        if osalause['words'][0]['analysis'][0]['partofspeech'] == 'J' and \
                osalause['words'][0]['text'].lower() in ["ja", "ning"] and \
                not osalause['words'][0]['text'][0].isupper():
            esimese_sona_lopp = osalause['words'][0]['end']+1 #lauset alustatakse kohast, kus esimese sõna lõppeb + tühik
            osalause = uuenda_lause(osalause['text'][esimese_sona_lopp:])
        
        #kui lause algab kirjavahemärgiga, jäetakse see ja tema järel olev tühik ära
        if osalause['words'][0]['analysis'][0]['partofspeech'] == 'Z':
            osalause = uuenda_lause(osalause['text'][1:].strip())
            
        try: #võib juhtuda, et nüüdseks pole enam ühtki sõna osalauses, seega 'try'
            #kui osalause algab verbiga, otsitakse lausest subjekti või verbile vastavat kindlat pronoomenit
            if osalause['words'][0]['analysis'][0]['partofspeech'] == 'V' and not osalause['text'][0].isupper():
                # ainult verbist koosnev lause jäetakse puutumatuks
                if len(osalause.words)!=1 and not (len(osalause.words)==2 and osalause['text'][-1]=="."): 
                    tegija = None 
                    #otsib tegijaks lauses olevat subjekti
                    subjektiotsing = tuvasta_subjekt(osalause['text'], pikk_lause['text'])
                    if subjektiotsing: #kui leiti subjekt: 
                        tegija = subjektiotsing[0] #määrab subjekti tegijaks
                        osalause['text'] = osalause['text'][:subjektiotsing[1]] + osalause['text'][subjektiotsing[2]+1:] #kustutab algsest osalause tekstist leitud subjekti
                    
                    else: #kui subjekti ei leitud, otsib, kas leidub verbile vastav kindel pronoomen
                        tegija = tuvasta_alus(osalause['words'][0]['analysis'])

                    if tegija!=None: #kui subjekt / kindel pronoomen leiti, võib selle lisada lause algusesse
                        osalause = uuenda_lause(tegija + " " + osalause['text'])

            #asesõnaga algavate lausete puhul võiks tulevikus asendada sobivaima sõnaga (viitealusega), hetkel pannakse sobivaim asesõna.
            elif osalause['words'][0]['analysis'][0]['partofspeech'] == 'P': 
                asendaja=osalause['words'][0]['text']
                vorm = osalause['words'][0]['analysis'][0]['form']
                
                esimese_sona_lopp = osalause['words'][0]['end'] #indeks, kus esimene sõna lõppeb

                #kui lause ei alga piisavalt selge asesõnaga või suure tähega, siis see asendatakse
                if osalause['words'][0]['analysis'][0]['lemma'] not in ['mina', 'sina', 'tema', 'meie', 'teie', 'nemad', 'see',
                                                                          'too', 'kõik', 'ise', 'mõni', 'sama', 'säärane', 
                                                                          'mõlema', 'üks', 'iga', 'keegi', 'selline', 'oma', 
                                                                          'kumb', 'mitu', 'miski', 'üksteise', 'missugune'] and \
                        not osalause['text'][0].isupper():
                    if osalause['words'][0]['analysis'][0]['lemma']=="mis":
                        asendaja = "See"
                        tegija=None
                    else:
                        try: #igas lauses ei pruugi olla verbi
                            #asendaja leitakse verbi järgi
                            verbiindeks = Text(osalause['text']).postags.index('V')
                            tegija = tuvasta_alus(osalause['words'][verbiindeks]['analysis'])
                            if tegija!=None: 
                                asendaja=tegija
                            #kui asendajat ei leitud, tuleb võtta "Tema"
                            else:
                                asendaja = 'Tema'
                                
                        except: #muul juhul tuleb valida "Tema"
                            asendaja = 'Tema'
                            tegija = None
                    
                    #asendaja lausesse panemine:
                    #võimalusel leitakse asendaja ainsus/mitmus tema viitealuse järgi
                    am = sg_pl(osalause['words'][0]['text'], pikk_lause)
                    if am: #kui leiti vorm, siis võib pronoomeni asendada
                        vorm = am +" "+ vorm.split(" ", 1)[1] #liidab ainsuse/mitmuse ülejäänud vormi tunnustega
                        uus_asendaja = synthesize(asendaja, vorm)
                        if len(uus_asendaja)==2: #võimalusel võetakse pikem variant (nt 'sest' vs 'sellest')
                            asendaja = uus_asendaja[1]
                        else:
                            asendaja =  uus_asendaja[0]
                        osalause = uuenda_lause(asendaja + osalause['text'][esimese_sona_lopp:])
                    else: #kui vormi ei leitud, tuleb see osalause liita eelmisega tagasi kokku
                        osalause = uuenda_lause(valjund_listina[-1][:-1] +", " + osalause['text'])
                        valjund_listina=valjund_listina[:-1]
            
            #Edasised toimingud lausega vastavalt selle algusele / lõpule
        
            #Sõnadega ....... või tegusõnadega, mille 'form' väärtus on 'maks' või 'des',
                #algav lause liidetakse eelmisega tagasi kokku
            if len(valjund_listina)>=1 and ((osalause['words'][0]['analysis'][0]['lemma'] in \
                                        ['kui', 'kas', 'kuidas', 'kus', 'kust', 'et', 'kuid', 'nagu', 'missugune', 'ehkki', 'ent', 
                                         'kuigi', 'ehk', 'miks', 'kuni', 'mil', 'vaid', 'sest', 'vist', 'aga', 'kuna', 'siis', 
                                        'kuivõrd', 'alates', 'mitu'] and not osalause['text'][0].isupper()) or \
                    osalause['words'][0]['analysis'][0]['form'] in ['maks', 'des'] or \
                    osalause['words'][0]['text'] in ['kuhu'] or \
                    (osalause['words'][0]['text'] in ['see', 'seda'] and (', see' in pikk_lause['text'] or ', seda' in pikk_lause['text']))):
                osalause = uuenda_lause(valjund_listina[-1][:-1] +", " + osalause['text'])
                valjund_listina=valjund_listina[:-1]
                

            #Sõnaga 'kui', 'kuna(s)', 'nagu', 'et' või fraasiga "Ainult kui", "Sel(lel) ajal kui", "Enne kui" algav, 
                #või sõnaga 'see' või 'seda' lõppev 
                #lause tuleb liita järgmisega
            if (len(valjund_listina)==0 and osalause['words'][0]['analysis'][0]['lemma'] in ['kui', 'kuna', 'kunas', 'nagu', 'et']) or \
                    re.search("(([Aa]inult)|([Ss]el(lel)? ajal)|([Ee]nne)) kui", osalause['text']) or \
                    osalause['words'][-2]['text'] in ['see', 'seda']:
                eelmisest = uuenda_lause(osalause['text'][:-1])
            
            #Sõnaga 'või', 'ega', lõppev lause tuleb liita järgmisega
            elif osalause['words'][-2]['text'] in ['või', 'ega']:
                eelmisest = uuenda_lause(osalause['text'][:-1])
    
                
            #ühesõnalise lause puhul tuleb see sõna liita eelmisele lausele või viia järgmise osalause algusesse
            if len(osalause['text'].split())==1 and eelmisest==None:
                if len(valjund_listina)>0:
                    osalause = uuenda_lause(valjund_listina[-1][:-1] +" ja " + osalause['text'])
                    valjund_listina=valjund_listina[:-1]
                else :
                    osalause=osalaused[o]

                valjund_listina.append(osalause['text'])
                eelmisest = None

            #Muul juhul: lause algaks suure tähega ja korrastatud osalause võib lisada väljundisse
            elif eelmisest==None: 
                osalause['text']=osalause['text'][0].capitalize()+osalause['text'][1:]
                if osalause['text'][-1]!='.':
                    osalause['text']=osalause['text'].strip()+'.'
                valjund_listina.append(osalause['text'])
                eelmisest = None
                
            o+=1
        except:
            o+=1
    
    #kui 'eelmine' ei ole tühi, kuid kõik osalaused on üle vaadatud, tuleb viimane osalause lisada lausete listi
    if eelmisest!=None and (len(valjund_listina)==0 or valjund_listina[-1] not in eelmisest):
        #lause algus suureks
        eelmisest['text']=eelmisest['text'][0].capitalize()+eelmisest['text'][1:]
        #lause lõppu punkt
        if eelmisest['words'][-1]['analysis'][0]['partofspeech']!='Z':
            if eelmisest['text'][-1]!='.':
                eelmisest['text'] = eelmisest['text']+"."
        elif eelmisest['words'][-1]['text'] in [',', ':', ';', ')', '-']:
            eelmisest['text'] = (eelmisest['text'][:-1]).strip()+"."
        #lisab listi
        valjund_listina.append(eelmisest['text'])
      
    valjund = ' '.join(valjund_listina) #ühendab listis olevad laused tühikutega eraldatuna üheks String-tüüpi sõneks.
            
    return valjund

#meetod 'lihtsustajasse' on vahendaja ühe lause ja selle lihtsustamise vahel, st siin leitakse algse lause osalaused.
def lihtsustajasse(sisend):
    sisend = Text(sisend)
    
    #eraldab osalaused ja lihtsustab sisendlause
    sisend = sisend.tag_clauses()
    osalaused = sisend.split_by('clauses')
    lihtsustatult = lihtsusta(osalaused, sisend)
        
    return lihtsustatult


#meetod 'sulgudega' lihtsustab sulge sisaldavat lauset
def sulgudega(sisendtekst):
    #leiab kõik sulgudes olevad kohas
    sulgudes = re.findall("\([^\(]*\)", sisendtekst)

    #eemaldab algsest lausest sulgudes teksti ning lihtsustab allesjäänut
    sulgudeta = sisendtekst
    for s in sulgudes:
        sulgudeta = re.sub("\("+s+"\)", '', sulgudeta)
    sulgudeta = lihtsustajasse(sulgudeta)

    #lisab lihtsustatud teksti sulgudes oleva tagasi
    vastus = sulgudeta
    for sulg in sulgudes:    
        #leiab algses lauses kuni 7 tähemärki enne ja pärast sulge
        enne = re.sub(sulg, '', (re.search("(.{,7})?"+sulg, sisendtekst)).group(0))
        parast = re.sub(sulg, '', (re.search(sulg+"(.{,7})?", sisendtekst)).group(0))

        try: #üritab lisada sulgudes teksti tagasi sellele eelnenu järgi. (sulgudes info on reeglina osalause lõpus)
            listina = vastus.split(enne[:-2])
            if listina[1][0]==" ": #keset lauset sulgude äravõtmisel jääb kahekordne tühik algusesse
                vastus = listina[0]+enne+sulg[1:]+listina[1][1:]
            else: # kui sulud olid vahetult enne kirjavahemärki, ei tekkinud üleliigset tühikut
                vastus = listina[0]+enne+sulg[1:]+listina[1]

        except: #kui sulgudes info on (osa)lause alguses, tuleb panna see info tagasi sellele järgneva alusel
            if parast:
                listina = vastus.split(parast[2:])
                vastus = listina[0]+sulg+parast[1:]+listina[1]

            else: #sobiva koha leidmatusel tagastatakse esialgne lause
                vastus = sisendtekst
    return vastus


#meetod 'saatelauseSVX' muudab vajadusel/võimalusel otsekõne saatelause sõnajärje eestipäraseks (s.o SVX)
def saatelauseSVX(saatelause):
    #loodavale Text-objektile lisatakse vajalikud kihid
    saatelause = Text(saatelause)
    saatelause.tag_syntax()
    listina=list(zip(saatelause.word_texts, saatelause['conll_syntax'], saatelause.postags))
    
    #korjab eraldi aluse, öeldise ja ülejäänud lause osad
    alus = ""
    subjekt = False #kui alust lausest ei leita, siis ei saa eraldi ka tema omadusi kasutada
    oeldis = None
    muu = ""
    for l in listina:
        if l[1]['parser_out'][0][0]=='ROOT':
            oeldis = l[0]
        elif l[1]['parser_out'][0][0]=='@SUBJ' and ('S' in saatelause.postags or 'H' in saatelause.postags or 'P' in saatelause.postags):
            alus = alus +" "+ l[0]
            subjekt = True
        elif l[1]['parser_out'][0][0]=='@AN>' and ('S' in saatelause.postags or 'H' in saatelause.postags or 'P' in saatelause.postags):
            alus = alus +" "+ l[0]
        elif l[1]['parser_out'][0][0]=='@NN>' and ('S' in saatelause.postags or 'H' in saatelause.postags or 'P' in saatelause.postags):
            alus = alus +" "+ l[0]
        elif '"' not in l[0]:
            muu = muu +" "+ l[0]

    if subjekt: #subjekti leidmisel võib moodustada õige sõnajärjega lause
        uus = alus + " " + oeldis + muu
    else: #subjekti leidmatusel tagastatakse esialgne tekst
        uus = saatelause['text']
        
    return uus

#meetod 'yhendaOtsekLause' ühendab kohandatud saatelause kohandatud otsekõnega ühtseks lauseks nii, et saatelause eelneks otsekõnele.
def yhendaOtsekLause(saatelause, otsekone):
    #korrigeerib saatelause 
    saatelause = saatelauseSVX(saatelause)
    saatelause = re.sub(" ?\.", ':', lihtsustajasse(saatelause))
    
    #lihtsustab otsekõne  
    otsekone = lihtsustajasse(otsekone)
    
    #paneb parandatud lause kokku
    vastuslause = saatelause+' "'+otsekone+'"'
    return vastuslause

#meetod 'jutumarkidega' analüüsib ja lihtsustab jutumärke sisaldava teksti.
def jutumarkidega(sisendtekst):
    #otsib erinevaid otsekõne variante
    mitteOtsek = re.search("([a-zöäüõ])?[^(\:)|,|\.] \".*\"( [a-zöäüõ])?", sisendtekst)
    eesSaatelause = re.search("[A-ZÖÄÜÕ]([^(\"|\.|\!|\?)])*\: \"[A-ZÖÄÜÕ]([^(\")])*(\.|\!|\?)\"(\!|\?|\.|,)?", sisendtekst)
    keskelSaatelause = re.search("\"[A-ZÖÄÜÕ].*(\,|\!|\?)\" ([^(\")])*, \".*(\.|\!|\?)\"", sisendtekst)
    tagaJaJargnebOtsek = re.search("\"[A-ZÖÄÜÕ].*(\,|\!|\?)\" ([^(\")])*\. \".*(\.|\!|\?)\"(\.|\!|\?)?", sisendtekst)
    tagaSaatelause = re.search("\"[A-ZÖÄÜÕ].*(\,|\!|\?)\" ([^(\"|\!|\?|\.)])*\.", sisendtekst)

    vastus = None
    ylejaak = None
    
    if not mitteOtsek:
        if eesSaatelause: #kui saatelause on ees, jääb kõik samaks; komaga lõppemise puhul erand
            vastus = eesSaatelause.group(0)
            #kui lause jätkub (otsekõne järel on koma), siis on vastuseks kõik kuni antud lause lõpuni
            if vastus[-1]==",":
                kogulause = re.search(vastus+" (\w| )*(\.|\!|\?)", sisendtekst)
                vastus = kogulause.group(0)
            if re.sub(vastus, '', sisendtekst) in vastus: #Nt lause 'Miks Jüri küsis minult: "Kas sa oled haige?"?' korral oleks muidu ylejaak=['', '?"?'] 
                ylejaak = ['', '']
            else:
                ylejaak = re.split(vastus, sisendtekst)

        elif keskelSaatelause: #keskel olev saatelause tuleb tuua ette ning otsekõne osad omavahel kokku liita
            #eraldab muutujatesse esimese ja teise otsekõne osa ning saatelause
            saatelause = keskelSaatelause.group(0)
            esimeneOtsek = re.search("\"[A-ZÖÄÜÕ].*(\,|\!|\?)\" [a-zöäüõ]", saatelause)
            saatelause = re.sub(esimeneOtsek.group(0)[:-2], '', saatelause)
            teineOtsek = re.search("\".*(\.|\!|\?)\"", saatelause)
            saatelause = re.sub(teineOtsek.group(0), '', saatelause)

            #salvestab vastuse ja leiab tekstiosa, mis ei sisalda antud lauset
            vastus = yhendaOtsekLause(saatelause, esimeneOtsek.group(0)[1:-3]+" "+teineOtsek.group(0)[1:-1])
            ylejaak = re.split(keskelSaatelause.group(0), sisendtekst)

        elif tagaJaJargnebOtsek: #keskele jääv saatelause tuua ette ning otsekõned kokku liita
            #eraldab muutujatesse esimese ja teise otsekõne osa ning saatelause
            saatelause = tagaJaJargnebOtsek.group(0)
            esimeneOtsek = re.search("\"[A-ZÖÄÜÕ].*(\,|\!|\?)\" ", saatelause)
            saatelause = re.sub(esimeneOtsek.group(0), '', saatelause)
            teineOtsek = re.search("\".*(\.|\!|\?)\"(\.|\!|\?)?", saatelause)
            saatelause = re.sub(teineOtsek.group(0), '', saatelause)

            #salvestab vastuse ja leiab tekstiosa, mis ei sisalda antud lauset
            vastus = yhendaOtsekLause(saatelause, esimeneOtsek.group(0)[1:-2]+" "+teineOtsek.group(0)[1:-1])
            ylejaak = re.split(tagaJaJargnebOtsek.group(0), sisendtekst)

        elif tagaSaatelause: #taga asuv saatelause tuleks selguse mõttes tuua ette
            #eraldab muutujatesse otsekõne ning saatelause
            saatelause = tagaSaatelause.group(0)
            esimeneOtsek = re.search("\"[A-ZÖÄÜÕ].*(\,|\!|\?)\" ", saatelause)
            saatelause = re.sub(esimeneOtsek.group(0), '', saatelause)

            #salvestab vastuse ja leiab tekstiosa, mis ei sisalda antud lauset
            vastus = yhendaOtsekLause(saatelause, esimeneOtsek.group(0)[1:-2])
            ylejaak = re.split(tagaSaatelause.group(0), sisendtekst)

    else: #tekstis esineb mõni pealkiri või tsitaat -> analüüsitakse ülejäänud tekst ja lisatakse jutumärkides olev info samasse kohta tagasi
        #leiab jutumärkides oleva info
        jutumargidKeskel = re.search("\".*\"", sisendtekst)
        jutumarkides = jutumargidKeskel.group(0)

        #eraldab jutumärkidest väljapoole jääva ning lihtustab seda
        muu= lihtsustajasse(''.join(re.sub(jutumarkides, '', sisendtekst)))

        #leiab algses lauses kuni 5 tähemärki enne ja pärast jutumärke
        enne = re.sub(jutumarkides, '', (re.search("(.{,5})?"+jutumarkides, sisendtekst)).group(0))
        parast = re.sub(jutumarkides, '', (re.search(jutumarkides+"(.{,5})?", sisendtekst)).group(0))

        if enne: #eelistatum on lisada eelneva teksti järgi jutumärkides olev tagasi
            try: #võib juhtuda, et endise tühiku asemel jutumärkide ees on nüüd punkt, seega 'try'
                listina = muu.split(enne)
                vastus = listina[0]+enne+jutumarkides+listina[1]
            except:
                listina = muu.split(enne[:-1])
                vastus = listina[0]+enne+jutumarkides+listina[1]
        elif parast: #vajadusel kasutatakse infot jutumärkidest hiljem asetsevat infot tagasipanekuks
            listina = muu.split(parast)
            vastus = jutumarkides+parast+listina[1]
        else: #muul juhul tagastatakse algne tekst
            vastus = sisendtekst
    
    return (vastus, ylejaak)


#meetod 'algus' analüüsib kasutaja antud sisendit ja saadab info vajalikule meetodile lihtsustamiseks.
def algus(sisendt):
    
    lihtne = "" #programmi tulemus kogutakse String-tüüpi muutujasse

    #sisendit analüüsitakse lõikude kaupa
    for sisendtekst in sisendt.split("\n"):
        
        if sisendtekst!='': 
            #ühtlustab jutumärkide tüübi
            if '”' in sisendtekst or '«' in sisendtekst:
                sisendtekst = re.sub('(«|»|“|”|„)', '"', sisendtekst)

            try:
                
                #jutumärkide esinemisel eraldab ja lihtsustab jutumärke sisaldavad laused
                if '"' in sisendtekst:
                    jutum, muu = jutumarkidega(sisendtekst)
                    if jutum == None: #tekst koosnebki ainult jutumärkides olevast -> lihtsustab jutumärkides olevat ja tagastab lihtsustatud tekst jutumärkides
                        lihtne = lihtne + '"'+lihtsustajasse(sisendtekst.strip()[1:-1])+'" '
                    elif muu == ['', ''] or muu == None: #teksti ainus lause oli jutumärkidega (otsekõnega / pealkirjaga / tsitaadiga)
                        lihtne = lihtne + jutum + " "
                    elif muu[0] == '': #jutumärkidega lause oli esimene lause
                        lihtne = lihtne + jutum + " " + algus(muu[1]) + " "
                    elif muu[1] == '': #jutumärkidega lause oli tagapool
                        lihtne = lihtne + algus(muu[0]) + jutum +" "
                    else: #jutumärkidega lause oli keset teksti
                        lihtne = lihtne + algus(muu[0]) + jutum +" "+ algus(muu[1]) + " "
                else:
                    #sisendi vajalik teisendus
                    sisendtekst = Text(sisendtekst)
                    #analüüsitakse iga lauset eraldi
                    for lause in sisendtekst.split_by('sentences'):
                        if ':' in lause.word_texts: #kooloniga lause, (mis ei sisalda otsekõnet,) tuleb jätta samasuguseks 
                            lihtne = lihtne + lause['text'] + " "
                                
                        elif '(' in lause.word_texts: #sulge sisaldava lause jaoks on eraldi meetod
                            lihtne = lihtne + sulgudega(lause['text']) + " "
                            
                        else: #muudel juhtudel saab lauset lihtsustada
                            lihtne = lihtne + lihtsustajasse(lause['text']) + " "

            except: #juhuks, kui lihtsustamine peaks luhtuma
                lihtne = lihtne + sisendtekst + " "
            
            lihtne = lihtne+"\n" #lisab lõigu lõppu reavahetuse
            
    return lihtne.strip("\n") #kõige viimase lõigu järele pole reavahetust vaja

#käsureaargumendi kasutamine (PHP jaoks):
"""if len(argv)>1:
    #eemaldatakse siinse programmi jaoks ebavajalikud sümbolid
    h = HTMLParser()
    programmisisend = (h.unescape(argv[1])).replace("\\;", "")
    programmisisend = (programmisisend).replace("\\", "")
    print(algus(programmisisend))
"""
#programmi käivitamine väljaspool serverit: 
#1. kommenteeri välja eelmised 5 koodirida ning faili alguses 2 rida koodi "veebis nltk kasutamiseks"
#2. Eemalda järgneva koodibloki ümber olevad jutumärgid
#3. käivita fail ning seejärel küsitakse sisendit

#küsib sisendteksti 

sisendtekst = input("Sisesta oma tekst ja vajuta Enter: \n")
print("\n", algus(sisendtekst))
