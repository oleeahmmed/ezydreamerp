        // Sheet functionality
        const openSheetBtn = document.getElementById('openSheetBtn');
        const closeSheetBtn = document.getElementById('closeSheetBtn');
        const sheet = document.getElementById('sheet');
        const sheetOverlay = document.getElementById('sheetOverlay');

        function openSheet() {
            sheetOverlay.classList.add('opacity-100', 'visible');
            sheet.classList.remove('translate-x-full');
            document.body.style.overflow = 'hidden';
        }

        function closeSheet() {
            sheetOverlay.classList.remove('opacity-100', 'visible');
            sheet.classList.add('translate-x-full');
            document.body.style.overflow = '';
        }

        openSheetBtn.addEventListener('click', openSheet);
        closeSheetBtn.addEventListener('click', closeSheet);
        sheetOverlay.addEventListener('click', closeSheet);

        // Close sheet when pressing Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !sheetOverlay.classList.contains('invisible')) {
                closeSheet();
            }
        });
