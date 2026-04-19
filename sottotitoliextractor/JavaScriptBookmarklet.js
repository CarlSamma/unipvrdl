(function() {
    'use strict';

    // Function to format time from seconds to HH:MM:SS,ms
    function formatTime(seconds) {
        const date = new Date(0);
        date.setSeconds(seconds);
        const timeString = date.toISOString().substr(11, 12);
        return timeString.replace('.', ',');
    }

    // Find the transcript container
    const transcriptContainer = document.getElementById('transcriptTabPane');
    if (!transcriptContainer) {
        return { error: 'Transcript container not found. Make sure you are on the "Sottotitoli" tab.' };
    }

    // Extract entries
    const entries = Array.from(transcriptContainer.querySelectorAll('li'));
    if (entries.length === 0) {
        return { error: 'No transcript entries found.' };
    }

    let srtContent = '';
    const extractedEntries = [];

    entries.forEach((entry, index) => {
        // Struttura reale Panopto:
        // <li>
        //   <div class="event-error">...</div>
        //   <div class="index-event-row">
        //     <div class="event-text"><span>TESTO</span></div>
        //     <div class="event-time">0:00</div>
        //   </div>
        // </li>

        const eventRow = entry.querySelector('.index-event-row');
        if (!eventRow) return;

        const eventText = eventRow.querySelector('.event-text');
        const eventTime = eventRow.querySelector('.event-time');

        if (!eventText || !eventTime) return;

        // Estrae testo (potrebbe essere in <span> o direttamente nel div)
        const textSpan = eventText.querySelector('span');
        const text = textSpan ? textSpan.textContent.trim() : eventText.textContent.trim();
        
        const timestampText = eventTime.textContent.trim();

        if (!text || !timestampText) return;

        // Parse timestamp (formato: "0:00" o "1:23:45")
        const timeParts = timestampText.split(':').map(Number);
        let startTimeSeconds = 0;
        if (timeParts.length === 3) { // HH:MM:SS
            startTimeSeconds = timeParts[0] * 3600 + timeParts[1] * 60 + timeParts[2];
        } else if (timeParts.length === 2) { // MM:SS
            startTimeSeconds = timeParts[0] * 60 + timeParts[1];
        }

        extractedEntries.push({
            start: startTimeSeconds,
            text: text
        });
    });

    if (extractedEntries.length === 0) {
        return { error: 'No valid transcript entries extracted.' };
    }

    // Genera SRT
    extractedEntries.forEach((entry, index) => {
        const nextEntry = extractedEntries[index + 1];
        const endTimeSeconds = nextEntry ? nextEntry.start : entry.start + 5;

        srtContent += `${index + 1}\n`;
        srtContent += `${formatTime(entry.start)} --> ${formatTime(endTimeSeconds)}\n`;
        srtContent += `${entry.text}\n\n`;
    });

    return { srt: srtContent };
})();