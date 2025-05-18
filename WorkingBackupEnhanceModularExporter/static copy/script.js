// static/script.js
document.addEventListener('DOMContentLoaded', function() {
    const chatListbox = document.getElementById('chat-listbox');
    const previewArea = document.getElementById('preview-area');
    const selectAllCb = document.getElementById('select-all-cb');
    const selectionCountSpan = document.getElementById('selection-count');
    const applyFilterBtn = document.getElementById('apply-filter-btn');
    const searchInput = document.getElementById('search');
    const dateFilterCb = document.getElementById('date_filter');
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');
    const exportForm = document.getElementById('export-form');
    const mergeButton = document.querySelector('button[name="merge_selected"]');
    const splitModeRadios = document.querySelectorAll('input[name="split_mode"]');
    const splitValueInput = document.querySelector('input[name="split_value"]');
    const folderModeRadios = document.querySelectorAll('input[name="folder_mode"]');

    async function updatePreview() {
        if (!chatListbox || chatListbox.selectedOptions.length !== 1) {
            previewArea.value = chatListbox?.selectedOptions.length > 1 ? '(Select only one chat to preview)' : '(Select a chat to preview)'; return;
        }
        const idx = chatListbox.selectedOptions[0].value; previewArea.value = 'Loading preview...';
        try {
            const resp = await fetch(`/preview?index=${idx}`); if (!resp.ok) throw new Error(`Server error: ${resp.statusText}`);
            const data = await resp.json(); previewArea.value = data.error ? `Error: ${data.error}` : data.preview;
        } catch (err) { previewArea.value = `Failed to load preview: ${err}`; console.error('Preview fetch error:', err); }
    }
    function updateSelectionCount() {
        if (!chatListbox || !selectionCountSpan || !selectAllCb || !mergeButton) return;
        const count = chatListbox.selectedOptions.length; const total = chatListbox.options.length;
        selectionCountSpan.textContent = `Selected: ${count}`; selectAllCb.checked = (count>0&&count===total); selectAllCb.indeterminate = (count>0&&count<total);
        const merging = count > 1; mergeButton.disabled = !merging;
        mergeButton.title = merging ? "Merges selected chats. Disables splitting & smart folders." : "Select >= 2 chats to merge";
        [...splitModeRadios, ...folderModeRadios, splitValueInput].forEach(el => { if(el) el.disabled = merging; });
        document.querySelectorAll('input[name="split_mode"], input[name="folder_mode"], input[name="split_value"]').forEach(el => { el?.closest('fieldset')?.classList.toggle('disabled-look', merging); });
    }
    function toggleSelectAll() { if (!chatListbox) return; const select = selectAllCb.checked; [...chatListbox.options].forEach(opt => opt.selected = select); updateSelectionCount(); updatePreview(); }
    function applyFilters() {
        const params = new URLSearchParams(); if (searchInput.value) params.append('search', searchInput.value);
        if (dateFilterCb.checked) { params.append('date_filter','on'); if(startDateInput.value)params.append('start_date', startDateInput.value); if(endDateInput.value)params.append('end_date', endDateInput.value); }
        window.location.search = params.toString();
    }
    if (chatListbox) chatListbox.addEventListener('change', () => { updateSelectionCount(); updatePreview(); });
    if (selectAllCb) selectAllCb.addEventListener('change', toggleSelectAll);
    if (applyFilterBtn) applyFilterBtn.addEventListener('click', applyFilters);
    if (searchInput) searchInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') { e.preventDefault(); applyFilters(); }});
    if (exportForm) {
        exportForm.addEventListener('submit', (e) => {
             if (chatListbox && chatListbox.selectedOptions.length === 0) { alert("Please select chats."); e.preventDefault(); return; }
             if (!exportForm.querySelector('input[name^="export_"]:checked')) { alert("Select export format."); e.preventDefault(); document.getElementById('export-options')?.scrollIntoView({behavior:'smooth'}); return; }
             const btn = e.submitter; if(btn) { btn.dataset.originalText = btn.innerText; btn.innerText='Processing...'; btn.disabled=true; }
        });
    }
    updateSelectionCount(); // Initial call
});