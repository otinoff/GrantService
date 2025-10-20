"""
Database Cleanup - REAL DELETION
ВНИМАНИЕ: Этот скрипт РЕАЛЬНО УДАЛЯЕТ данные из базы!
"""

from database_garbage_collection import cleanup_database, verify_cleanup

if __name__ == '__main__':
    print("\n" + "="*80)
    print("REAL DATABASE CLEANUP - REALNOE UDALENIE DANNYH")
    print("="*80)
    print("\nVNIMANIE! Sejchas budet vypolneno REALNOE UDALENIE!")
    print("\nChto budet udaleno:")
    print("  - 79 pustyh sessij bez otvetov")
    print("  - 59 sessij testovyh polzovatelej")
    print("  - 5 nezavershennyh issledovanij")
    print("  - 1 grant s pustym content")
    print("  - 1 grant application bez grant")
    print("\nITOGO: 145 zapisej\n")
    print("="*80)

    response = input("\nVvedite 'DELETE' dlya podtverzhdeniya: ")

    if response.strip() == 'DELETE':
        print("\nVypolnyayu REALNOE UDALENIE...\n")
        cleanup_database(dry_run=False)

        print("\nProverka rezultatov...\n")
        verify_cleanup()

        print("\n[SUCCESS] OCHISTKA ZAVERSHENA USPESHNO!\n")
    else:
        print("\n[CANCEL] Otmeneno polzovatelem\n")
