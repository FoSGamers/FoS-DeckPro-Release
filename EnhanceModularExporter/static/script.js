// static/script.js (SSE Progress Handling - COMPLETE AND VERIFIED - Batch 4)
document.addEventListener('DOMContentLoaded', function() {
    // --- Element References ---
    const chatListbox=document.getElementById('chat-listbox');
    const previewArea=document.getElementById('preview-area');
    const selectAllCb=document.getElementById('select-all-cb');
    const selectionCountSpan=document.getElementById('selection-count');
    const applyFilterBtn=document.getElementById('apply-filter-btn');
    const searchInput=document.getElementById('search');
    const dateFilterCb=document.getElementById('date_filter');
    const startDateInput=document.getElementById('start_date');
    const endDateInput=document.getElementById('end_date');
    const exportForm=document.getElementById('export-form');
    const mergeButton=document.querySelector('button[name="merge_selected"]');
    const exportButton=document.querySelector('button[name="export_selected"]');
    const splitModeRadios=document.querySelectorAll('input[name="split_mode"]');
    const splitValueInput=document.querySelector('input[name="split_value"]');
    const folderModeRadios=document.querySelectorAll('input[name="folder_mode"]');
    const flashMessagesDiv=document.getElementById('flash-messages');
    // Progress elements
    const progressContainer=document.getElementById('progress-container');
    const progressLogArea=document.getElementById('progress-log-area');
    const progressBar=document.getElementById('progress-bar');
    const downloadLinkContainer=document.getElementById('download-link-container');

    let progressEventSource = null; // Variable to hold the EventSource connection

    // --- Functions ---
    async function updatePreview(){
        if(!chatListbox||chatListbox.selectedOptions.length!==1){previewArea.value=chatListbox?.selectedOptions.length>1?'(Select only one chat to preview)':'(Select a chat to preview)';return}
        const idx=chatListbox.selectedOptions[0].value;previewArea.value='Loading preview...';try{const resp=await fetch(`/preview?index=${idx}`);let errorMsg=`Server error:${resp.statusText}`;if(!resp.ok){try{const errData=await resp.json();if(errData&&errData.error){errorMsg=`Server Error:${errData.error}`}}catch(parseError){}throw new Error(errorMsg)}const data=await resp.json();previewArea.value=data.error?`Error:${data.error}`:data.preview||"(Preview unavailable)"}catch(err){previewArea.value=`Failed preview:${err}`;console.error('Preview fetch error:',err)}
    }

    function updateSelectionCount(){
        if(!chatListbox||!selectionCountSpan||!selectAllCb||!mergeButton||!exportButton)return;const count=chatListbox.selectedOptions.length,total=chatListbox.options.length;selectionCountSpan.textContent=`Selected:${count}`;selectAllCb.checked=(count>0&&count===total);selectAllCb.indeterminate=(count>0&&count<total);exportButton.disabled=count===0;const mergingPossible=count>1;mergeButton.disabled=!mergingPossible;mergeButton.title=mergingPossible?"Merges selected. Disables split/folder.":"Select >=2 chats";const disableOptions=mergingPossible;[...splitModeRadios,...folderModeRadios,splitValueInput].forEach(el=>{if(el)el.disabled=disableOptions});document.querySelectorAll('fieldset').forEach(fieldset=>{const hasMergeSensitiveControl=fieldset.querySelector('input[name="split_mode"],input[name="folder_mode"],input[name="split_value"]');if(hasMergeSensitiveControl){fieldset.classList.toggle('disabled-look',disableOptions)}});
    }

    function toggleSelectAll(){if(!chatListbox)return;const sel=selectAllCb.checked;[...chatListbox.options].forEach(opt=>opt.selected=sel);updateSelectionCount();updatePreview()}

    function applyFilters(){const p=new URLSearchParams;o.value&&p.append("search",o.value),i.checked&&(p.append("date_filter","on"),c.value&&p.append("start_date",c.value),s.value&&p.append("end_date",s.value)),window.location.search=p.toString()} // Renamed conflicting vars

    function clearStatusMessage() {
        const existingStatus = flashMessagesDiv?.querySelector('.status-message');
        if (existingStatus) existingStatus.remove();
    }

    function showStatusMessage(message, type = 'info') {
        if (!flashMessagesDiv) return;
        clearStatusMessage(); // Clear previous status before showing new one
        const div = document.createElement('div');
        div.classList.add('flash', type, 'status-message');
        div.textContent = message;
        flashMessagesDiv.prepend(div); // Add to top
        // Optionally fade out info messages after a delay
        if (type === 'info' || type === 'success') {
            setTimeout(() => {
                div.style.opacity = '0';
                setTimeout(() => div.remove(), 500); // Remove after fade
            }, 5000); // 5 second delay
        }
    }

    function addProgressLog(message, type = 'info') {
        if (!progressLogArea) return;
        const p = document.createElement('p');
        const timeStamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        p.textContent = `[${timeStamp}] ${message}`;
        if (type === 'error') p.style.color = '#842029'; // Match flash error color
        if (type === 'warning') p.style.color = '#664d03'; // Match flash warning color
        if (type === 'success') p.style.color = '#0f5132'; // Match flash success color
        progressLogArea.appendChild(p);
        progressLogArea.scrollTop = progressLogArea.scrollHeight; // Auto-scroll
    }

    function updateProgressBar(percent) {
        if (!progressBar) return;
        progressBar.value = percent;
    }

    function resetExportUI(showError = false) {
        if (exportButton) { exportButton.innerText = 'Export Selected'; exportButton.disabled = chatListbox.selectedOptions.length === 0; }
        if (mergeButton) { mergeButton.innerText = 'Merge Selected'; mergeButton.disabled = chatListbox.selectedOptions.length <= 1; }
        // Only hide progress container if no persistent error message is shown
        if (progressContainer && !showError) progressContainer.style.display = 'none';
        if (!showError) clearStatusMessage(); // Clear info/success messages
    }

    // --- Event Listeners ---
    if(chatListbox)chatListbox.addEventListener('change',()=>{updateSelectionCount();updatePreview()});
    if(selectAllCb)selectAllCb.addEventListener('change',toggleSelectAll);
    if(applyFilterBtn)applyFilterBtn.addEventListener('click',applyFilters);
    if(searchInput)searchInput.addEventListener('keypress',e=>{if(e.key==='Enter'){e.preventDefault();applyFilters()}});

    // --- Modified Form submission for Fetch and SSE ---
    if(exportForm){
        exportForm.addEventListener('submit', async (event) => {
            event.preventDefault(); // STOP standard form submission
            clearStatusMessage(); // Clear previous flash/status messages

            if (chatListbox && chatListbox.selectedOptions.length === 0) { alert("Select chats."); return; }
            if (!exportForm.querySelector('input[name^="export_"]:checked')) { alert("Select format."); document.getElementById('export-options')?.scrollIntoView({behavior:'smooth'}); return; }

            const submitButton = event.submitter;
            const isMerge = submitButton.name === 'merge_selected';

            // Disable buttons & Show Progress Area
            if(submitButton) { submitButton.disabled = true; submitButton.innerText = 'Starting...';}
            if(exportButton) exportButton.disabled = true;
            if(mergeButton) mergeButton.disabled = true;
            if(progressContainer) progressContainer.style.display = 'block'; // Show progress area
            if(progressLogArea) progressLogArea.innerHTML = ''; // Clear old logs
            if(progressBar) progressBar.value = 0; // Reset progress bar
            if(downloadLinkContainer) downloadLinkContainer.innerHTML = ''; // Clear old download links
            addProgressLog('Export process initiating...');

            // Gather form data into JSON payload
            const formData = new FormData(exportForm);
            const selectedIndices = formData.getAll('selected_chats').map(Number);
            const formats = {};
            document.querySelectorAll('#export-options input[name^="export_"]:checked').forEach(cb => {
                formats[cb.name.replace('export_', '')] = true;
            });
            const options = {
                split_mode: formData.get('split_mode'),
                split_value: parseInt(formData.get('split_value') || '10', 10),
                folder_mode: formData.get('folder_mode'),
                anonymize: formData.has('anonymize'),
                leet_speak: formData.has('leet_speak'),
                use_chatid_filename: formData.has('use_chatid_filename'),
                html_embed_css: formData.has('html_embed_css'),
                is_merge: isMerge
            };
            const startData = { selected_indices: selectedIndices, formats: formats, options: options };

            // --- Start Export Process ---
            try {
                const startResponse = await fetch('/start-export', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(startData)
                });

                if (!startResponse.ok) {
                    const errorData = await startResponse.json().catch(() => ({ error: "Unknown start error" }));
                    throw new Error(errorData.error || `Server error: ${startResponse.statusText}`);
                }
                const startResult = await startResponse.json();
                const jobId = startResult.job_id;
                if (!jobId) throw new Error("Server did not return job ID.");

                addProgressLog(`Background job started (ID: ${jobId.substring(0, 8)}...). Waiting for updates...`);
                if(submitButton) submitButton.innerText = 'Processing...'; // Update button text

                // --- Connect to SSE Stream ---
                if (progressEventSource) progressEventSource.close(); // Close old connection if any
                progressEventSource = new EventSource(`/export-progress/${jobId}`);

                progressEventSource.onmessage = function(event) {
                    try {
                        const data = JSON.parse(event.data);
                        if (data.type === 'progress' || data.type === 'warning' || data.type === 'info') {
                            addProgressLog(data.message, data.type);
                            if (data.percent !== undefined) updateProgressBar(data.percent);
                        } else if (data.type === 'complete') {
                            addProgressLog(data.message, 'success'); updateProgressBar(100);
                            if (downloadLinkContainer) {
                                const link = document.createElement('a'); link.href = `/download/${jobId}`;
                                link.textContent = `Download Export Result`; link.classList.add('download-button');
                                downloadLinkContainer.innerHTML = ''; downloadLinkContainer.appendChild(link);
                            }
                            progressEventSource.close(); resetExportUI();
                        } else if (data.type === 'error') {
                            addProgressLog(`ERROR: ${data.message}`, 'error'); showStatusMessage(`Export failed: ${data.message}`, 'error');
                            progressEventSource.close(); resetExportUI(true);
                        } else if (data.type === 'final') {
                            addProgressLog('Server signal: Task ended.'); progressEventSource.close();
                            // Reset UI only if not already completed/errored
                             const jobStatusElement = downloadLinkContainer?.querySelector('a');
                             const errorFlash = flashMessagesDiv?.querySelector('.flash.error'); // Check for persistent error flash
                             if (!jobStatusElement && !errorFlash) {
                                 resetExportUI();
                             }
                        }
                    } catch (e) { console.error("SSE parse error:", e, "Data:", event.data); addProgressLog("Bad progress update.", "error"); }
                };

                progressEventSource.onerror = function(error) {
                    console.error("SSE Connection Error:", error); addProgressLog("Connection lost.", "error");
                    showStatusMessage("Connection Error getting progress.", "error");
                    if (progressEventSource) progressEventSource.close(); // Ensure closed on error
                    resetExportUI(true); // Assume failure
                };

            } catch (error) { // Catch errors from the initial /start-export fetch
                console.error("Error starting export:", error); showStatusMessage(`Failed to start: ${error}`, 'error');
                resetExportUI(true); // Reset UI on initial failure
            }
        }); // End form submit listener
    } // End if(exportForm)

    // --- Initial page load setup ---
    updateSelectionCount(); // Set initial button states etc.

}); // End DOMContentLoaded