const scanProgressBarContainer = document.getElementById('scanProgressBarContainer');
const scanProgressBar = document.getElementById('scanProgressBar');
const scanProgressText = document.getElementById('scanProgressText');
const element = document.querySelector('.video-feed');

function hideBackground() {
    element.style.backgroundImage = 'none';
}

function showBackground() {
    element.style.backgroundImage = 'url(/static/no_signal.png)';
}

function triggerAutofocus(camId) {
    fetch(`/autofocus/${camId}`)
        .then(response => {
            if (!response.ok) throw new Error(`Kamera ${camId} nije dostupna`);
            console.log(`Autofokus kamera ${camId} pokrenut`);
        })
        .catch(error => console.error(error));
}

function updateFocus(camId, value) {
    const formData = new FormData();
    formData.append("value", value);

    fetch(`/set_focus/${camId}`, {
        method: "POST",
        body: formData
    })
    .then(response => {
        if (!response.ok) throw new Error("Greška u postavljanju fokusa");
        document.getElementById(`focus-value-${camId}`).textContent = value;
    })
    .catch(error => {
        console.error(error);
    });
}

function updateScanProgress() {
    fetch('/scan_status')
        .then(response => response.json())
        .then(data => {
            if (data.scan_in_progress) {
                scanProgressBarContainer.style.display = 'block';
                const percentage = (data.current_scan_step / data.total_scan_steps) * 100;
                scanProgressBar.style.width = percentage + '%';
                scanProgressBar.textContent = Math.round(percentage) + '%';
                scanProgressText.textContent = `${data.current_scan_step}/${data.total_scan_steps} slike`;
            } else {
                scanProgressBarContainer.style.display = 'none';
                scanProgressText.textContent = '';
            }
        })
        .catch(error => console.error('Greška dohvaćanja statusa:', error));
}

setInterval(updateScanProgress, 2000);
updateScanProgress();
