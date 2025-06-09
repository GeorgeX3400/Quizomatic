# Quizomatic

Quizomatic este o aplicație ce are ca scop eficientizarea procesului de învățare prin utilizarea AI. Utilizatorii pot trimite către LLM diverse materiale (documente (docx, pdf), prezentări Powerpoint), pe baza cărora aceștia pot face prompt-uri sau genera quiz-uri ce pot fi personalizate.

## User Stories

- **1. Ca user**, vreau să îmi creez cont pentru a-mi păstra discuțiile cu LLM-ul, precum și materialele trimise.
- **2. Ca utilizator**, vreau să încarc documente (PDF, Word sau text) astfel încât sistemul să poată analiza conținutul.
- **3. Ca utilizator**, vreau ca aplicația să extragă conceptele și rezumatele cheie din materialele încărcate astfel încât să pot revizui eficient conținutul.
- **4. Ca utilizator**, vreau ca sistemul să genereze întrebări cu răspunsuri multiple din materialele încărcate astfel încât să îmi pot testa cunoștințele.
- **5. Ca utilizator**, vreau ca sistemul să creeze întrebări de tip adevărat/fals bazate pe materiale astfel încât să pot avea o opțiune rapidă de evaluare.
- **6. Ca utilizator**, vreau să selectez nivelul de dificultate (ușor, mediu, dificil) pentru testele generate astfel încât să mă pot provoca adecvat.
- **7. Ca utilizator**, vreau să personalizez numărul de întrebări din test astfel încât să se potrivească cu timpul meu disponibil.
- **8. Ca utilizator**, vreau să rezolv testele direct în aplicație astfel încât să îmi pot urmări progresul.
- **9. Ca utilizator**, vreau să primesc feedback imediat pentru răspunsurile mele astfel încât să învăț din greșeli.
- **10. Ca utilizator**, vreau ca sistemul să evidențieze zonele mele de slăbiciune pe baza performanței mele la teste pentru a mă concentra pe îmbunătățirea anumitor subiecte.
- **11. Ca utilizator**, vreau să revizuiesc explicații detaliate pentru fiecare întrebare după ce termin testul astfel încât să îmi îmbunătățesc cunoștințele.

## Diagrame UML

Diagramele UML pentru proiect se găsesc mai jos:
 - [Diagrama conceptuală pentru baza de date](https://www.mermaidchart.com/raw/9f2a1368-f6b4-4884-9e9b-b81d6e7ad943?theme=light&version=v0.1&format=svg)
 - [Diagrama workflow-ului](https://www.mermaidchart.com/raw/c73fab0e-d293-42cc-84c4-8aa928e6eb21?theme=light&version=v0.1&format=svg)

## Utilizarea Tool-urilor de AI
În dezvoltarea proiectului nostru am folosit ChatGPT și Github Copilot. 
Scopul prinicpal al acestora a fost cel de debugging. 
Cele 2 modele de AI și-au îmbunătățit răspunsurile pe măsură ce le ofeream informații relevante problemelor întâlnite. În lipsa acestora, nu au dat niște răspunsuri ajutătoare. 
### Exemple de probleme ale răspunsurilor:
 - Github Copilot: atunci când îi ziceam de o problema întălnită într-un fișier pe care nu l-a primit drept context, acesta halucina, spunând că nu este de fapt nici o problemă în codul care a crăpat;
 - ChatGPT: la o problemă zisă în cod, a răspuns cu o serie de probleme care ar putea fi în cod, nereușind să o spună pe cea care era de fapt.
### Cum am corectat greșelile făcute de modelele de AI:
 - Github Copilot: am dat în context toate fișierele care aveau cod implicat în eroarea respectivă;
 - ChatGPT: am dat în prompt codul care a fost executat ce a produs eroarea.

 Pentru ambele modele, am descris în mod detaliat cum am produs eroarea (ex: ce cereri am făcut la backend, ce operații am făcut la UI-ul din frontend). 
