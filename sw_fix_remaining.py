#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fix remaining 59 untranslated entries in Swahili PO file.
These entries have mojibake, backslash escapes, or other encoding issues
that prevented them from matching the standard translation dictionary.
"""
import polib
import os
import sys

def main():
    po_path = os.path.join(os.path.dirname(__file__), 'locale', 'sw', 'LC_MESSAGES', 'django.po')

    print(f"Opening PO file: {po_path}")
    po = polib.pofile(po_path)

    untranslated_before = len(po.untranslated_entries())
    print(f"Untranslated before: {untranslated_before}")

    applied = 0

    for entry in po.untranslated_entries():
        msgid = entry.msgid
        translation = None

        # Entry 1: participant count
        if msgid.strip() == '%(count)s participant':
            translation = "\n                Mshiriki %(count)s\n                "

        # Entry 2: Ex: 50-80€ (with mojibake euro sign)
        elif 'Ex: 50-80' in msgid:
            translation = "Mfano: 50-80€"

        # Entry 3: Âge (mojibake for Âge)
        elif msgid == 'Âge' or msgid == '\u00c3\u201aage' or msgid.startswith('\u00c3') and 'ge' in msgid and len(msgid) < 8:
            translation = "Umri"

        # Entry 4: Frère/Sœur (mojibake)
        elif 'Fr' in msgid and 'ur' in msgid and ('Å' in msgid or 'œ' in msgid or 'Soe' in msgid):
            translation = "Ndugu"

        # Entry 5: équipe(s)
        elif msgid == 'équipe(s)' or msgid == '\u00e9quipe(s)':
            translation = "timu"

        # Entry 6: Ex: Blessure d\'
        elif msgid.startswith("Ex: Blessure d"):
            translation = "Mfano: Jeraha la"

        # Entry 7: Chaque catégorie peut fonctionner en mode Équipe...
        elif 'peut fonctionner en mode' in msgid:
            translation = "Kila kundi linaweza kufanya kazi katika hali ya Timu au Mtu binafsi kwa uhuru."

        # Entry 8: équipes
        elif msgid == 'équipes' or msgid == '\u00e9quipes':
            translation = "timu"

        # Entry 9: Ce type de compétition est utilisé par %(counter)s...
        elif '%(counter)s' in msgid and 'suppression' in msgid:
            translation = "\n                            Aina hii ya mashindano inatumiwa na mashindano %(counter)s. \n                            Kufuta hakupendekezwi.\n                        "

        # Entry 10: Pas d\'
        elif msgid == "Pas d\\":
            translation = "Hakuna"

        # Entry 11: Votre navigateur ne supporte pas l\'
        elif 'navigateur ne supporte pas' in msgid:
            translation = "Kivinjari chako hakitumii"

        # Entry 12: Impossible d\'
        elif msgid == "Impossible d\\":
            translation = "Haiwezekani"

        # Entry 13: Phase de test en cours...
        elif 'Phase de test en cours' in msgid:
            translation = "Awamu ya majaribio inaendelea (Juni 1-30, 2025) \u2022 \n        Uzinduzi rasmi: Julai 1, 2025 \u2022 \n        "

        # Entry 14: Vous devez être responsable de club (mojibake)
        elif 'responsable de club' in msgid and 'acc' in msgid and 'page' in msgid:
            translation = "Lazima uwe msimamizi wa klabu kufikia ukurasa huu. Tafadhali unda klabu au wasiliana na msimamizi kuunganishwa na klabu iliyopo."

        # Entry 15: Aucun juge ou arbitre n'a été trouvé (mojibake)
        elif 'juge ou arbitre' in msgid and 'trouv' in msgid:
            translation = "Hakuna hakimu au mwamuzi aliyepatikana katika klabu yako. Unaweza kuongeza sifa kwa watendaji wako kutoka kwenye wasifu wao."

        # Entry 16: Un excellent coach avec une pédagogie (mixed mojibake)
        elif 'excellent coach avec une' in msgid:
            translation = "Kocha bora na ufundishaji uliobadilishwa kwa kila mwanafunzi. Makini sana na maelezo ya ufundi na daima anapatikana kwa maelezo ya ziada."

        # Entry 17: Grâce à son enseignement (mixed mojibake)
        elif 'enseignement rigoureux mais bienveillant' in msgid:
            translation = "Shukrani kwa ufundishaji wake mkali lakini wa huruma, nimeweza kuendelea haraka. Kozi zinatofautiana na daima ni za kuvutia."

        # Entry 18: Aucune assignation trouvée pour ce juge
        elif 'Aucune assignation trouv' in msgid and 'juge' in msgid:
            translation = "Hakuna mgawo uliopatikana kwa hakimu huyu."

        # Entry 19: {} a été retiré de la liste des juges ({} assignation(s)
        elif 'retir' in msgid and 'liste des juges' in msgid and 'assignation' in msgid:
            translation = "{} ameondolewa kwenye orodha ya mahakimu (mgawo {} umefutwa)."

        # Entry 20: {} a été retiré de la liste des juges.
        elif 'retir' in msgid and 'liste des juges' in msgid and 'assignation' not in msgid:
            translation = "{} ameondolewa kwenye orodha ya mahakimu."

        # Entry 21: La catégorie {} a été retirée avec succès.
        elif 'cat' in msgid and 'retir' in msgid and 'succ' in msgid:
            translation = "Kundi {} limeondolewa kwa mafanikio."

        # Entry 22: La catégorie {} a été ajoutée avec succès.
        elif 'cat' in msgid and 'ajout' in msgid and 'succ' in msgid:
            translation = "Kundi {} limeongezwa kwa mafanikio."

        # Entry 23: Les catégories ont été mises à jour avec succès.
        elif 'cat' in msgid and 'mises' in msgid and 'jour' in msgid:
            translation = "Makundi yamesasishwa kwa mafanikio."

        # Entry 24: Catégories invalides.
        elif 'gories invalides' in msgid:
            translation = "Makundi batili."

        # Entry 25: L'inscription a été approuvée avec succès.
        elif 'inscription' in msgid and 'approuv' in msgid and 'succ' in msgid:
            translation = "Usajili umeidhinishwa kwa mafanikio."

        # Entry 26: L'inscription de {} a été supprimée.
        elif 'inscription de {}' in msgid and 'supprim' in msgid:
            translation = "Usajili wa {} umefutwa."

        # Entry 27: %(name)s ajouté(e) au podium en position %(position)s.
        elif 'podium en position' in msgid:
            translation = "%(name)s ameongezwa kwenye podium katika nafasi %(position)s."

        # Entry 28: %(name)s retiré(e) du podium.
        elif 'retir' in msgid and 'podium' in msgid:
            translation = "%(name)s ameondolewa kwenye podium."

        # Entry 29: ID de catégorie manquant
        elif 'ID de cat' in msgid and 'manquant' in msgid:
            translation = "Kitambulisho cha kundi kinakosekana"

        # Entry 30: Catégorie non trouvée
        elif 'gorie non trouv' in msgid and len(msgid) < 35:
            translation = "Kundi halijapatikana"

        # Entry 31: Données manquantes
        elif 'es manquantes' in msgid and len(msgid) < 25:
            translation = "Data inayokosekana"

        # Entry 32: Cette catégorie est déjà planifiée
        elif 'gorie est d' in msgid and 'planifi' in msgid:
            translation = "Kundi hili tayari limepangwa"

        # Entry 33: Catégorie ajoutée au planning
        elif 'gorie ajout' in msgid and 'planning' in msgid:
            translation = "Kundi limeongezwa kwenye ratiba"

        # Entry 34: ID tatami manquant
        elif 'ID tatami manquant' in msgid:
            translation = "Kitambulisho cha tatami kinakosekana"

        # Entry 35: Félicitations ! Votre club a été créé avec succès.
        elif 'licitations' in msgid and 'club' in msgid and 'cr' in msgid and 'succ' in msgid:
            translation = "Hongera! Klabu yako imeundwa kwa mafanikio."

        # Entry 36: Accès refusé scanner QR codes (mojibake)
        elif 'scanner des QR codes' in msgid:
            translation = "Ufikiaji umekataliwa: Lazima uwe msimamizi wa klabu '{}' kutambaza misimbo ya QR. Wasiliana na mmiliki wa klabu ({}) kupata ruhusa."

        # Entry 37: DIPLÔME D'EXCELLENCE (mojibake)
        elif "DIPL" in msgid and "EXCELLENCE" in msgid:
            translation = "CHETI CHA UBORA"

        # Entry 38: Cet examen ne peut pas être supprimé (mojibake)
        elif 'examen' in msgid and 'supprim' in msgid and 'inscriptions' in msgid:
            translation = "Mtihani huu hauwezi kufutwa kwa sababu una usajili. Tafadhali sitisha mtihani badala ya kuufuta."

        # Entry 39: Paiement à réception de facture (mojibake)
        elif 'ception de facture' in msgid and 'nalit' in msgid:
            translation = "Malipo yanapokea ankara.\nKuchelewa kwa malipo kutasababisha adhabu ya 3% ya jumla ya kiasi.\nAsante kwa imani yako."

        # Entry 40: Paiement dû sous 30 jours (mojibake)
        elif 'sous 30 jours' in msgid:
            translation = "Malipo yanahitajika ndani ya siku 30 tangu tarehe ya kutolewa. Adhabu za kuchelewa zinatumika kulingana na masharti ya jumla."

        # Entry 41-46: Vietnamese scoring terms (mojibake)
        elif 'point' in msgid.lower() and ('Tu' in msgid or 'iá»' in msgid or 'Ã\x90' in msgid or 'Ná»' in msgid):
            if '¼' in msgid or 'Tu' in msgid and '¼' in msgid:
                translation = "¼ pointi (Phân Tu Điểm)"
            elif '½' in msgid and 'Ná»' in msgid:
                translation = "½ pointi (Nửa Điểm)"
            elif '1.5' in msgid:
                translation = "Pointi 1.5 (Một Điểm Dưới)"
            elif '2 points' in msgid:
                translation = "Pointi 2 (Hai Điểm)"
            elif '1 point' in msgid:
                translation = "Pointi 1 (Một Điểm)"
            else:
                translation = None

        # Entry 46: Kém Điểm (Retrait de ½ point)
        elif 'Retrait de' in msgid and 'point' in msgid:
            translation = "Kém Điểm (Kuondoa ½ pointi)"

        # Entry 47: Loại (Disqualification immédiate)
        elif 'Disqualification imm' in msgid:
            translation = "Loại (Kutokuwa na sifa mara moja)"

        # Entry 48: La date d\'
        elif msgid == "La date d\\":
            translation = "Tarehe ya"

        # Entry 49-56: Pour créer/modifier/supprimer des factures/méthodes/transactions (mojibake with rôles)
        elif 'les suivants' in msgid and 'dération' in msgid and 'rÃ´les' in msgid:
            if 'créer des factures' in msgid:
                translation = "Ili kuunda ankara, lazima uwe na moja ya majukumu yafuatayo: Msimamizi wa shirikisho, Msimamizi wa klabu, Kocha, au Meneja. Wasiliana na msimamizi wako kupata ruhusa zinazofaa."
            elif 'modifier des factures' in msgid:
                translation = "Ili kurekebisha ankara, lazima uwe na moja ya majukumu yafuatayo: Msimamizi wa shirikisho, Msimamizi wa klabu, Kocha, au Meneja. Wasiliana na msimamizi wako kupata ruhusa zinazofaa."
            elif 'supprimer des factures' in msgid:
                translation = "Ili kufuta ankara, lazima uwe na moja ya majukumu yafuatayo: Msimamizi wa shirikisho, Msimamizi wa klabu, Kocha, au Meneja. Wasiliana na msimamizi wako kupata ruhusa zinazofaa."
            elif 'créer des méthodes' in msgid or 'er des m' in msgid and 'thodes' in msgid and 'cr' in msgid:
                translation = "Ili kuunda njia za malipo, lazima uwe na moja ya majukumu yafuatayo: Msimamizi wa shirikisho, Msimamizi wa klabu, Kocha, au Meneja. Wasiliana na msimamizi wako kupata ruhusa zinazofaa."
            elif 'modifier des méthodes' in msgid or 'modifier des m' in msgid and 'thodes' in msgid:
                translation = "Ili kurekebisha njia za malipo, lazima uwe na moja ya majukumu yafuatayo: Msimamizi wa shirikisho, Msimamizi wa klabu, Kocha, au Meneja. Wasiliana na msimamizi wako kupata ruhusa zinazofaa."
            elif 'supprimer des méthodes' in msgid or 'supprimer des m' in msgid and 'thodes' in msgid:
                translation = "Ili kufuta njia za malipo, lazima uwe na moja ya majukumu yafuatayo: Msimamizi wa shirikisho, Msimamizi wa klabu, Kocha, au Meneja. Wasiliana na msimamizi wako kupata ruhusa zinazofaa."
            elif 'créer des transactions' in msgid or 'er des transactions' in msgid and 'cr' in msgid:
                translation = "Ili kuunda miamala, lazima uwe na moja ya majukumu yafuatayo: Msimamizi wa shirikisho, Msimamizi wa klabu, Kocha, au Meneja. Wasiliana na msimamizi wako kupata ruhusa zinazofaa."
            elif 'modifier des transactions' in msgid:
                translation = "Ili kurekebisha miamala, lazima uwe na moja ya majukumu yafuatayo: Msimamizi wa shirikisho, Msimamizi wa klabu, Kocha, au Meneja. Wasiliana na msimamizi wako kupata ruhusa zinazofaa."

        # Entry 57: Cette organisation ne peut pas être supprimée (mojibake)
        elif 'organisation' in msgid and 'supprim' in msgid and 'affiliations' in msgid:
            translation = "Shirika hili haliwezi kufutwa kwa sababu lina ushirika. Tafadhali ondoa ushirika wote kabla ya kufuta shirika."

        # Entry 58: À définir (mojibake)
        elif 'finir' in msgid and len(msgid) < 20 and ('Ã' in msgid or 'À' in msgid):
            translation = "Itabainishwa"

        # Entry 59: État (mojibake)
        elif msgid == 'Ã‰tat' or ('tat' in msgid and len(msgid) < 8 and 'Ã' in msgid):
            translation = "Hali"

        if translation:
            entry.msgstr = translation
            applied += 1

    po.save(po_path)
    print(f"\nApplied {applied} additional translations.")

    # Verify
    po2 = polib.pofile(po_path)
    untranslated_after = len(po2.untranslated_entries())
    translated_after = len(po2.translated_entries())
    print(f"\nAfter fix:")
    print(f"  Translated: {translated_after}")
    print(f"  Untranslated: {untranslated_after}")

    if untranslated_after > 0:
        print(f"\nRemaining untranslated:")
        for e in po2.untranslated_entries():
            print(f"  - {repr(e.msgid[:100])}")

if __name__ == '__main__':
    main()
