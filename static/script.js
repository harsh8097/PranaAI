const form = document.getElementById('documentUploadForm');
const reportReaderForm = document.getElementById('reportReaderForm');
const fileInput = document.getElementById('documentFile');
const reportReaderFileInput = document.getElementById('reportReaderFile');
const resultBox = document.getElementById('validationResult');
const reportReaderResultBox = document.getElementById('reportReaderResult');
const removeFileButton = document.getElementById('removeFileButton');
const assistantQuestion = document.getElementById('assistantQuestion');
const askAssistantButton = document.getElementById('askAssistantButton');
const assistantOutput = document.getElementById('assistantOutput');
const videoAnalysisForm = document.getElementById('videoAnalysisForm');
const videoFileInput = document.getElementById('videoFile');
const videoAnalysisResult = document.getElementById('videoAnalysisResult');
const analyzeVideoButton = document.getElementById('analyzeVideoButton');
const monitorVideo = document.getElementById('monitorVideo');
const monitorCanvas = document.getElementById('monitorCanvas');
const cameraPlaceholder = document.getElementById('cameraPlaceholder');
const startCameraButton = document.getElementById('startCameraButton');
const stopCameraButton = document.getElementById('stopCameraButton');
const monitorStatus = document.getElementById('monitorStatus');
const pulseWaveform = document.getElementById('pulseWaveform');

// Cardiac monitor & condition elements
const heartRateValue = document.getElementById('heartRateValue');
const rhythmTag = document.getElementById('rhythmTag');
const pulseHeartIcon = document.getElementById('pulseHeartIcon');
const signalQualityChip = document.getElementById('signalQualityChip');
const patientConditionCard = document.getElementById('patientConditionCard');
const patientConditionBadge = document.getElementById('patientConditionBadge');
const hemodynamicTag = document.getElementById('hemodynamicTag');
const conditionHeading = document.getElementById('conditionHeading');
const conditionSummary = document.getElementById('conditionSummary');
const conditionStateText = document.getElementById('conditionStateText');
const conditionClassText = document.getElementById('conditionClassText');
const conditionAdviceText = document.getElementById('conditionAdviceText');
const simNormalBtn = document.getElementById('simNormalBtn');
const simTachyBtn = document.getElementById('simTachyBtn');
const simBradyBtn = document.getElementById('simBradyBtn');
const simResetBtn = document.getElementById('simResetBtn');

let cameraStream = null;
let monitorTimer = null;
let pulseSamples = [];
let lastSignalQualityUpdate = 0;
let lastReportId = '';
let simAnimationId = null;
let simPhase = 0;
let currentSimBpm = 0;

/* -------------------------------------------------------------
   Hero Activity Buttons & Smooth Section Scrolling
------------------------------------------------------------- */
function setupActivityNavigation() {
  const links = document.querySelectorAll('.activity-button, .site-nav a[href^="#"], .hero-actions a[href^="#"], .tool-card[href^="#"]');
  links.forEach(link => {
    link.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href');
      if (!targetId || !targetId.startsWith('#')) return;
      const targetElement = document.querySelector(targetId);
      if (targetElement) {
        e.preventDefault();
        targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });

        const targetPanel = targetElement.querySelector('.panel') || targetElement;
        targetPanel.classList.remove('panel-highlight');
        void targetPanel.offsetWidth;
        targetPanel.classList.add('panel-highlight');

        const focusInput = targetElement.querySelector('input[type="file"], textarea, button:not([disabled])');
        if (focusInput) {
          setTimeout(() => focusInput.focus({ preventScroll: true }), 450);
        }
      }
    });
  });
}

// Show selected filename on drop zones
if (fileInput) {
  fileInput.addEventListener('change', function () {
    const parent = fileInput.closest('.drop-zone');
    if (parent && fileInput.files[0]) {
      const titleEl = parent.querySelector('strong');
      if (titleEl) titleEl.textContent = `Selected: ${fileInput.files[0].name}`;
    }
  });
}

if (reportReaderFileInput) {
  reportReaderFileInput.addEventListener('change', function () {
    const parent = reportReaderFileInput.closest('.drop-zone');
    if (parent && reportReaderFileInput.files[0]) {
      const titleEl = parent.querySelector('strong');
      if (titleEl) titleEl.textContent = `Selected: ${reportReaderFileInput.files[0].name}`;
    }
  });
}

if (videoFileInput) {
  videoFileInput.addEventListener('change', function () {
    const label = document.querySelector('label[for="videoFile"]');
    if (label && videoFileInput.files[0]) {
      label.textContent = `Selected: ${videoFileInput.files[0].name}`;
    }
  });
}

/* -------------------------------------------------------------
   Document Validation & Direct Parameter Extraction
------------------------------------------------------------- */
function renderDiagnosticReport(data, fileName) {
  const tests = data.tests || [];
  const rows = tests.map(item => {
    const isAbnormal = item.status === 'outside stated range';
    const badgeClass = isAbnormal ? 'danger' : (item.reference_range ? 'success' : 'neutral');
    return `
      <tr style="${isAbnormal ? 'background: #fff4f4;' : ''}">
        <td><strong>${escapeHTML(item.label)}</strong></td>
        <td><strong>${escapeHTML(item.value)}</strong></td>
        <td>${escapeHTML(item.unit || '—')}</td>
        <td>${escapeHTML(item.reference_range || 'Not stated')}</td>
        <td><span class="badge ${badgeClass}">${escapeHTML(item.status)}</span></td>
      </tr>
    `;
  }).join('');

  let conditionBanner = '';
  if (data.patient_condition) {
    const pc = data.patient_condition;
    conditionBanner = `
      <div class="patient-report-condition ${escapeHTML(pc.tone || 'neutral')}">
        <h5>${escapeHTML(pc.badge || 'Patient Condition Assessment')}</h5>
        <p>${escapeHTML(pc.summary || '')}</p>
      </div>
    `;
  }

  let summaryHtml = '';
  if (data.summary) {
    summaryHtml = `<p style="margin: 8px 0; font-size: 0.84rem; color: #334338;"><strong>Clinical Summary:</strong> ${escapeHTML(data.summary)}</p>`;
  }

  const abnormalCount = (data.abnormal_values || []).length;
  const metaBar = `
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px solid #e2e8f0;">
      <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
        <span class="badge success">✓ Parameters Extracted</span>
        ${abnormalCount > 0 ? `<span class="badge danger">${abnormalCount} Outside Normal Range</span>` : '<span class="badge success">All Stated Ranges Normal</span>'}
        ${fileName ? `<span style="font-family: var(--font-mono); font-size: 0.72rem; color: var(--gray-500);">Source: ${escapeHTML(fileName)}</span>` : ''}
      </div>
      <span class="module-code">Total Biomarkers: ${tests.length}</span>
    </div>
  `;

  const tableHtml = tests.length > 0 ? `
    <table>
      <thead>
        <tr><th>Test Parameter</th><th>Value</th><th>Unit</th><th>Biological Reference Interval</th><th>Status</th></tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  ` : `<p style="margin: 10px 0; font-size: 0.84rem; color: #475569;">${data.file_type === 'pdf' ? 'No numerical lab parameters were detected in this document. (Document may be a diagnostic radiology scan, discharge summary, or prescription).' : 'Document validated. Ready for clinical interpretation.'}</p>`;

  const nextStepHtml = `
    <div class="next-step-card">
      <div class="next-step-info">
        <span class="step-badge">STEP 03 READY · CLINICAL ASSISTANT GROUNDED</span>
        <strong>Proceed to AI consultation grounded in these ${tests.length} parameters</strong>
      </div>
      <div style="display: flex; gap: 8px; flex-wrap: wrap;">
        <button type="button" class="primary-btn" onclick="scrollToAssistantWithQuery()">
          <span>Consult AI Copilot</span>
          <span class="btn-arrow" aria-hidden="true">→</span>
        </button>
        <a href="#monitor" class="secondary-btn" style="min-height: 38px; font-size: 0.8rem; padding: 6px 14px;">
          <span>Open Cardiac Monitor ↓</span>
        </a>
      </div>
    </div>
  `;

  return `
    ${metaBar}
    ${conditionBanner}
    ${summaryHtml}
    ${tableHtml}
    ${nextStepHtml}
  `;
}

window.scrollToReportReader = function() {
  const reportReaderSection = document.getElementById('report-reader');
  if (reportReaderSection) {
    reportReaderSection.scrollIntoView({ behavior: 'smooth' });
    const panel = reportReaderSection.querySelector('.panel') || reportReaderSection;
    panel.classList.remove('panel-highlight');
    void panel.offsetWidth;
    panel.classList.add('panel-highlight');
  }
};

window.scrollToAssistantWithQuery = function() {
  const assistantSection = document.getElementById('assistant');
  if (assistantSection) {
    assistantSection.scrollIntoView({ behavior: 'smooth' });
    const panel = assistantSection.querySelector('.panel') || assistantSection;
    panel.classList.remove('panel-highlight');
    void panel.offsetWidth;
    panel.classList.add('panel-highlight');
  }
  if (assistantQuestion) {
    if (!assistantQuestion.value || assistantQuestion.value.trim() === '') {
      assistantQuestion.value = 'Please provide a clinical overview of these extracted lab parameters and explain any findings that require medical attention.';
    }
    assistantQuestion.focus();
  }
};

// Wire change report file button in Module 02
const changeReportFileBtn = document.getElementById('changeReportFileBtn');
if (changeReportFileBtn) {
  changeReportFileBtn.addEventListener('click', function () {
    const readerBanner = document.getElementById('readerActiveDocBanner');
    const readerBadge = document.getElementById('readerModuleBadge');
    if (readerBanner) readerBanner.style.display = 'none';
    if (reportReaderForm) reportReaderForm.style.display = 'block';
    if (readerBadge) {
      readerBadge.textContent = 'Diagnostic PDF & Scans';
      readerBadge.className = 'badge neutral';
    }
  });
}

if (form) {
  form.addEventListener('submit', async function (event) {
    event.preventDefault();
    const file = fileInput.files[0];

    if (!file) {
      updateResult('No file selected. Please choose a medical document.', 'neutral');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    resultBox.className = 'result-box neutral';
    resultBox.innerHTML = '<h4>Validating and Extracting Diagnostic Parameters...</h4><p>Analyzing document integrity, normalizing font encoding, and extracting laboratory test values and reference intervals.</p>';

    try {
      const response = await fetch('/api/validate-document', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok && data.accepted) {
        lastReportId = data.report_id || '';
        
        // 1. Update Module 01 with clear validation confirmation and forward alert
        resultBox.className = 'result-box success';
        resultBox.innerHTML = `
          <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #e2e8f0;">
            <div>
              <span class="badge success" style="margin-right: 6px;">✓ Document Validated</span>
              <strong>${escapeHTML(data.status)}</strong>
            </div>
            <span class="module-code">Confidence: ${Math.round((data.confidence || 0.96) * 100)}%</span>
          </div>
          <p style="margin-bottom: 8px; font-size: 0.85rem; color: var(--gray-700);">${escapeHTML(data.reason || 'Medical record integrity authenticated.')}</p>
          <div class="validation-forwarding-alert">
            <div class="validation-forwarding-copy">
              <span class="active-pulse-dot"></span>
              <span><strong>Document automatically forwarded to Module 02.</strong> Diagnostic parameters and biological ranges loaded directly without duplicate upload.</span>
            </div>
            <button type="button" class="quick-action-btn" onclick="scrollToReportReader()" style="padding: 6px 12px; font-size: 0.76rem;">View In Lab Reader ↓</button>
          </div>
        `;

        // 2. Automatically populate and configure Module 02 (Report Reader) - No upload needed!
        const readerBanner = document.getElementById('readerActiveDocBanner');
        const readerDocName = document.getElementById('readerDocName');
        const readerBadge = document.getElementById('readerModuleBadge');

        if (readerBanner && readerDocName) {
          readerDocName.textContent = file.name;
          readerBanner.style.display = 'block';
        }
        if (reportReaderForm) {
          reportReaderForm.style.display = 'none'; // Hide duplicate upload form
        }
        if (readerBadge) {
          readerBadge.textContent = 'Active Document Loaded';
          readerBadge.className = 'badge success';
        }

        if (reportReaderResultBox) {
          reportReaderResultBox.className = 'result-box success';
          reportReaderResultBox.innerHTML = renderDiagnosticReport(data, file.name);
        }

        // Try syncing file to report reader input behind the scenes
        try {
          const transfer = new DataTransfer();
          transfer.items.add(file);
          if (reportReaderFileInput) reportReaderFileInput.files = transfer.files;
        } catch (e) {}

        // 3. Setup pre-filled question and grounded badge for assistant (Module 03)
        const assistantGroundedBadge = document.getElementById('assistantGroundedBadge');
        if (assistantGroundedBadge) {
          assistantGroundedBadge.textContent = `Grounded: ${file.name}`;
        }
        if (assistantQuestion) {
          if (data.abnormal_values && data.abnormal_values.length > 0) {
            assistantQuestion.value = 'Which test parameters were identified outside normal ranges and what clinical precautions are recommended?';
          } else {
            assistantQuestion.value = 'Please provide a clear clinical overview of this extracted medical report and confirm reference ranges.';
          }
        }

        // 4. Smoothly scroll directly to Module 02 (Next Step)
        setTimeout(() => {
          scrollToReportReader();
        }, 380);

      } else {
        updateResult(
          `<strong>${escapeHTML(data.alert || 'Document validation check failed')}</strong><br/>${escapeHTML(data.reason)}`,
          'danger'
        );
      }
    } catch (error) {
      updateResult('A validation connection error occurred. Please check that the server is running and try again.', 'danger');
    }
  });
}

if (removeFileButton) {
  removeFileButton.addEventListener('click', function () {
    fileInput.value = '';
    const parent = fileInput.closest('.drop-zone');
    if (parent) {
      const titleEl = parent.querySelector('strong');
      if (titleEl) titleEl.textContent = 'Choose or Drag Medical Document Here';
    }
    updateResult('No document has been validated yet.', 'neutral');
  });
}

/* -------------------------------------------------------------
   Report Reader Form (Manual Upload Fallback)
------------------------------------------------------------- */
if (reportReaderForm) {
  reportReaderForm.addEventListener('submit', async function (event) {
    event.preventDefault();
    const file = reportReaderFileInput.files[0];
    if (!file) {
      updateReaderResult('Please choose a valid medical document to extract.', 'neutral');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    updateReaderResult('<strong>Extracting lab report data...</strong><p>Parsing tabular values, units, reference intervals, and patient condition.</p>', 'neutral');

    try {
      const response = await fetch('/api/report-reader', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();

      if (response.ok && data.accepted) {
        lastReportId = data.report_id || '';

        const readerBanner = document.getElementById('readerActiveDocBanner');
        const readerDocName = document.getElementById('readerDocName');
        const readerBadge = document.getElementById('readerModuleBadge');

        if (readerBanner && readerDocName) {
          readerDocName.textContent = file.name;
          readerBanner.style.display = 'block';
        }
        reportReaderForm.style.display = 'none';
        if (readerBadge) {
          readerBadge.textContent = 'Active Document Loaded';
          readerBadge.className = 'badge success';
        }

        reportReaderResultBox.className = 'result-box success';
        reportReaderResultBox.innerHTML = renderDiagnosticReport(data, file.name);

        const assistantGroundedBadge = document.getElementById('assistantGroundedBadge');
        if (assistantGroundedBadge) {
          assistantGroundedBadge.textContent = `Grounded: ${file.name}`;
        }

        if (assistantQuestion) {
          if (data.abnormal_values && data.abnormal_values.length > 0) {
            assistantQuestion.value = 'Which test parameters were identified outside normal ranges and what clinical precautions are recommended?';
          } else {
            assistantQuestion.value = 'Please provide a clear clinical overview of this extracted medical report and confirm reference ranges.';
          }
        }
      } else {
        updateReaderResult(`<strong>${escapeHTML(data.alert || 'Unable to extract report.')}</strong><p>${escapeHTML(data.message || '')}</p>`, 'danger');
      }
    } catch (error) {
      updateReaderResult('The report reader could not process the file. Please ensure the server is active and try again.', 'danger');
    }
  });
}

/* -------------------------------------------------------------
   AI Report Assistant
------------------------------------------------------------- */
if (askAssistantButton) {
  askAssistantButton.addEventListener('click', async function () {
    const question = assistantQuestion.value.trim();
    if (!question) {
      updateAssistantOutput('Please enter a question about the report.', 'neutral');
      return;
    }
    if (!lastReportId) {
      updateAssistantOutput('Please upload and extract a validated report in the Report Reader above before asking questions.', 'neutral');
      return;
    }

    updateAssistantOutput('Analyzing the uploaded report and grounding response...', 'neutral');

    try {
      const response = await fetch('/api/ask-assistant', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          report_id: lastReportId,
        }),
      });

      const data = await response.json();
      updateAssistantOutput(data.answer || data.error || 'No answer could be generated.', 'neutral');
    } catch (error) {
      updateAssistantOutput('Could not reach the assistant service. Please check that Flask is running and retry.', 'danger');
    }
  });
}

/* -------------------------------------------------------------
   Video Analysis Form
------------------------------------------------------------- */
if (videoAnalysisForm) {
  videoAnalysisForm.addEventListener('submit', async function (event) {
    event.preventDefault();
    const file = videoFileInput.files[0];
    if (!file) {
      updateVideoResult('Select a video before starting analysis.', 'danger');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    analyzeVideoButton.disabled = true;
    analyzeVideoButton.textContent = 'Processing...';
    updateVideoResult('Uploading and checking video frames. This may take a moment.', 'neutral');

    try {
      const response = await fetch('/api/video-analysis', { method: 'POST', body: formData });
      const data = await response.json();
      if (!response.ok || !data.accepted) {
        updateVideoResult(data.alert || 'Video processing failed. Please try another file.', 'danger');
      } else if (data.heart_rate_bpm === null) {
        updateVideoResult(
          `<strong>${data.message}</strong><p>Signal quality: ${data.signal_quality}. ${data.warning}</p><p>Duration: ${data.duration_seconds}s; frames processed: ${data.frames_processed}.</p>`,
          'neutral'
        );
      } else {
        updateVideoResult(
          `<strong>Experimental heart-rate estimate: ${data.heart_rate_bpm} BPM</strong><p>Signal quality: ${data.signal_quality}. ${data.warning}</p><p>Duration: ${data.duration_seconds}s; frames processed: ${data.frames_processed}.</p>`,
          'success'
        );
      }
    } catch (error) {
      updateVideoResult('Could not reach the video analysis service. Check that the Flask server is running, then retry.', 'danger');
    } finally {
      analyzeVideoButton.disabled = false;
      analyzeVideoButton.textContent = 'Analyze video';
    }
  });
}

/* -------------------------------------------------------------
   Live Camera Monitoring
------------------------------------------------------------- */
if (startCameraButton && stopCameraButton && monitorVideo && monitorCanvas) {
  startCameraButton.addEventListener('click', startCameraMonitoring);
  stopCameraButton.addEventListener('click', stopCameraMonitoring);
  window.addEventListener('pagehide', stopCameraMonitoring);
}

async function startCameraMonitoring() {
  stopSimulatedCardiacWave();
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    updateMonitorStatus('Camera access is unavailable. Use a supported browser over HTTPS or localhost.', 'danger');
    return;
  }

  startCameraButton.disabled = true;
  updateMonitorStatus('Requesting camera permission…', 'neutral');
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
      audio: false,
    });
    monitorVideo.srcObject = cameraStream;
    await monitorVideo.play();
    cameraPlaceholder.hidden = true;
    startCameraButton.disabled = true;
    stopCameraButton.disabled = false;
    pulseSamples = [];
    lastSignalQualityUpdate = 0;
    monitorTimer = window.setInterval(sampleCameraSignal, 1000 / 15);
    updateMonitorStatus('Camera active. Center your forehead in the guide and remain still for at least 20 seconds.', 'neutral');
    if (signalQualityChip) signalQualityChip.innerHTML = 'Signal: <strong>Acquiring...</strong>';
  } catch (error) {
    startCameraButton.disabled = false;
    const messages = {
      NotAllowedError: 'Camera permission was denied. Allow camera access in your browser settings and try again.',
      NotFoundError: 'No camera was found. Connect a camera and try again.',
      NotReadableError: 'The camera is busy or could not be read. Close other apps using it and retry.',
      OverconstrainedError: 'The camera does not support the requested settings. Try another camera.',
      SecurityError: 'Camera access is blocked by browser security settings. Open this app on localhost or HTTPS.',
    };
    updateMonitorStatus(
      messages[error && error.name] || 'Could not start the camera. Check browser camera permissions and connected device.',
      'danger'
    );
  }
}

function stopCameraMonitoring() {
  if (monitorTimer !== null) {
    window.clearInterval(monitorTimer);
    monitorTimer = null;
  }
  if (cameraStream) {
    cameraStream.getTracks().forEach(track => track.stop());
    cameraStream = null;
  }
  if (monitorVideo) {
    monitorVideo.srcObject = null;
  }
  if (cameraPlaceholder) cameraPlaceholder.hidden = false;
  if (startCameraButton) startCameraButton.disabled = false;
  if (stopCameraButton) stopCameraButton.disabled = true;
  if (monitorStatus) updateMonitorStatus('Monitoring stopped. Camera frames remained local to this browser.', 'neutral');
  if (signalQualityChip) signalQualityChip.innerHTML = 'Signal: <strong>Idle</strong>';
}

function sampleCameraSignal() {
  if (!monitorVideo.videoWidth || !monitorVideo.videoHeight) return;
  const context = monitorCanvas.getContext('2d', { willReadFrequently: true });
  const width = monitorVideo.videoWidth;
  const height = monitorVideo.videoHeight;
  monitorCanvas.width = width;
  monitorCanvas.height = height;

  const roiWidth = Math.floor(width * 0.32);
  const roiHeight = Math.floor(height * 0.12);
  const roiX = Math.floor((width - roiWidth) / 2);
  const roiY = Math.floor(height * 0.22);
  context.drawImage(monitorVideo, roiX, roiY, roiWidth, roiHeight, 0, 0, 64, 24);
  const pixels = context.getImageData(0, 0, 64, 24).data;
  let greenSum = 0;
  let brightnessSum = 0;
  for (let index = 0; index < pixels.length; index += 4) {
    greenSum += pixels[index + 1];
    brightnessSum += (pixels[index] + pixels[index + 1] + pixels[index + 2]) / 3;
  }
  const pixelCount = pixels.length / 4;
  const greenMean = greenSum / pixelCount;
  const brightness = brightnessSum / pixelCount;
  const now = performance.now();
  pulseSamples.push({ time: now, green: greenMean, brightness });

  const sampleWindowMs = 22000;
  pulseSamples = pulseSamples.filter(sample => now - sample.time <= sampleWindowMs);
  drawPulseWaveform(pulseSamples);

  if (now - lastSignalQualityUpdate < 3000) return;
  lastSignalQualityUpdate = now;
  if (brightness < 35 || brightness > 225) {
    updateMonitorStatus('Lighting is too dark or overexposed. Adjust room light and keep forehead in the guide.', 'warning');
    if (signalQualityChip) signalQualityChip.innerHTML = 'Signal: <strong>Poor Lighting</strong>';
    return;
  }
  if (pulseSamples.length < 20 * 15) {
    const secs = Math.floor(pulseSamples.length / 15);
    updateMonitorStatus(`Collecting arterial signal: ${secs} of 20 seconds. Stay still and keep forehead in the guide.`, 'neutral');
    if (signalQualityChip) signalQualityChip.innerHTML = `Signal: <strong>Buffering (${secs}/20s)</strong>`;
    return;
  }

  const estimate = estimatePulseBpm(pulseSamples);
  if (estimate === null) {
    updateMonitorStatus('Insufficient signal quality for a reliable estimate. Minimize movement and maintain steady lighting.', 'warning');
    if (signalQualityChip) signalQualityChip.innerHTML = 'Signal: <strong>Low SNR</strong>';
    return;
  }

  updateMonitorStatus(`Experimental heart-rate estimate: ${estimate} BPM. This is not a diagnostic measurement.`, 'success');
  if (signalQualityChip) signalQualityChip.innerHTML = 'Signal: <strong>Locked (Good)</strong>';

  // Update cardiac monitor UI
  if (estimate >= 60 && estimate <= 100) {
    setPatientCardiacState(estimate, 'Rhythm: Regular Sinus (Normocardia)', 'success', 'Hemodynamic: Stable', 'Patient Cardiovascular Health Condition', 'Patient pulse rate is well within normal adult resting physiological limits (60–100 BPM).', 'Well Condition (Normocardia)', 'Maintain balanced hydration and normal activity.');
  } else if (estimate > 100) {
    setPatientCardiacState(estimate, 'Rhythm: Sinus Tachycardia (Elevated)', 'warning', 'Hemodynamic: Elevated Demand', 'Elevated Resting Pulse Detected', 'Heart rate is currently above the standard adult resting range (>100 BPM). Consider resting comfortably.', 'Tachycardia / Elevated Rate', 'Rest seated, breathe slowly, and verify reading after 5 minutes.');
  } else {
    setPatientCardiacState(estimate, 'Rhythm: Sinus Bradycardia (Low / Athletic)', 'warning', 'Hemodynamic: Low Resting', 'Low Resting Pulse Detected', 'Heart rate is below standard adult resting range (<60 BPM), typical of well-conditioned athletes or resting state.', 'Bradycardia / Low Resting', 'If accompanied by dizziness or fatigue, consult a healthcare provider.');
  }
}

function estimatePulseBpm(samples) {
  const values = samples.map(sample => sample.green);
  const count = values.length;
  const elapsedSeconds = (samples[count - 1].time - samples[0].time) / 1000;
  if (count < 300 || elapsedSeconds < 19) return null;
  const sampleRate = (count - 1) / elapsedSeconds;

  const meanTime = (count - 1) / 2;
  const meanValue = values.reduce((sum, value) => sum + value, 0) / count;
  let covariance = 0;
  let timeVariance = 0;
  for (let index = 0; index < count; index += 1) {
    covariance += (index - meanTime) * (values[index] - meanValue);
    timeVariance += (index - meanTime) ** 2;
  }
  const slope = timeVariance ? covariance / timeVariance : 0;
  const detrended = values.map((value, index) => value - (meanValue + slope * (index - meanTime)));
  const standardDeviation = Math.sqrt(detrended.reduce((sum, value) => sum + value * value, 0) / count);
  if (!Number.isFinite(standardDeviation) || standardDeviation < 0.03) return null;

  const motionChanges = samples.slice(1).map((sample, index) => Math.abs(sample.brightness - samples[index].brightness));
  const averageMotion = motionChanges.reduce((sum, value) => sum + value, 0) / Math.max(1, motionChanges.length);
  if (averageMotion > 8) return null;

  let bestPower = 0;
  let bestFrequency = 0;
  const bandPowers = [];
  for (let frequency = 0.7; frequency <= 3.0001; frequency += 0.025) {
    let real = 0;
    let imaginary = 0;
    for (let index = 0; index < count; index += 1) {
      const window = 0.5 - 0.5 * Math.cos((2 * Math.PI * index) / (count - 1));
      const angle = (2 * Math.PI * frequency * index) / sampleRate;
      const weighted = detrended[index] * window;
      real += weighted * Math.cos(angle);
      imaginary -= weighted * Math.sin(angle);
    }
    const power = real * real + imaginary * imaginary;
    bandPowers.push(power);
    if (power > bestPower) {
      bestPower = power;
      bestFrequency = frequency;
    }
  }
  const sortedPowers = [...bandPowers].sort((left, right) => left - right);
  const medianPower = sortedPowers[Math.floor(sortedPowers.length / 2)] || 0;
  if (!medianPower || bestPower / medianPower < 5) return null;

  const bpm = Math.round(bestFrequency * 60);
  return bpm >= 42 && bpm <= 180 ? bpm : null;
}

function drawPulseWaveform(samples) {
  if (!pulseWaveform) return;
  const context = pulseWaveform.getContext('2d');
  const width = pulseWaveform.width;
  const height = pulseWaveform.height;
  context.clearRect(0, 0, width, height);

  // Background grid
  context.strokeStyle = 'rgba(31, 58, 47, 0.4)';
  context.lineWidth = 1;
  for (let x = 0; x < width; x += 40) {
    context.beginPath();
    context.moveTo(x, 0);
    context.lineTo(x, height);
    context.stroke();
  }
  for (let y = 0; y < height; y += 30) {
    context.beginPath();
    context.moveTo(0, y);
    context.lineTo(width, y);
    context.stroke();
  }

  if (samples.length < 2) return;

  const values = samples.map(sample => sample.green);
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const range = maximum - minimum || 1;

  context.strokeStyle = '#4ecca3';
  context.lineWidth = 2.2;
  context.beginPath();
  values.forEach((value, index) => {
    const x = (index / (values.length - 1)) * width;
    const y = height - ((value - minimum) / range) * (height - 20) - 10;
    if (index === 0) context.moveTo(x, y);
    else context.lineTo(x, y);
  });
  context.stroke();
}

/* -------------------------------------------------------------
   Cardiac Simulation & Condition Assessment
------------------------------------------------------------- */
function setPatientCardiacState(bpm, rhythm, tone, hemodynamic, heading, summary, classification, advice) {
  if (heartRateValue) heartRateValue.textContent = bpm || '--';
  if (rhythmTag) rhythmTag.textContent = rhythm;
  if (hemodynamicTag) hemodynamicTag.textContent = hemodynamic;
  if (conditionHeading) conditionHeading.textContent = heading;
  if (conditionSummary) conditionSummary.textContent = summary;
  if (conditionStateText) conditionStateText.textContent = classification;
  if (conditionClassText) conditionClassText.textContent = tone === 'success' ? 'Normal / Well' : (tone === 'danger' ? 'High Risk' : (tone === 'warning' ? 'Observation Required' : 'Awaiting Signal'));
  if (conditionAdviceText) conditionAdviceText.textContent = advice;

  if (patientConditionBadge) {
    patientConditionBadge.className = `condition-pill ${tone}`;
    patientConditionBadge.innerHTML = `<span class="status-indicator"></span> Patient Condition: ${classification}`;
  }

  if (pulseHeartIcon) {
    if (bpm) {
      const dur = (60 / bpm).toFixed(2);
      pulseHeartIcon.style.animation = `heartBeat ${dur}s infinite ease-in-out`;
      pulseHeartIcon.style.color = tone === 'success' ? '#2ecc71' : (tone === 'warning' ? '#f39c12' : '#e74c3c');
    } else {
      pulseHeartIcon.style.animation = 'none';
      pulseHeartIcon.style.color = '#758a7e';
    }
  }
}

function startSimulatedCardiacWave(bpm) {
  stopSimulatedCardiacWave();
  stopCameraMonitoring();
  currentSimBpm = bpm;

  const canvas = pulseWaveform;
  if (!canvas) return;
  const context = canvas.getContext('2d');
  const width = canvas.width;
  const height = canvas.height;

  function renderWave() {
    simPhase += (bpm / 60) * 0.045;
    context.clearRect(0, 0, width, height);

    // Grid
    context.strokeStyle = 'rgba(31, 58, 47, 0.4)';
    context.lineWidth = 1;
    for (let x = 0; x < width; x += 40) {
      context.beginPath();
      context.moveTo(x, 0);
      context.lineTo(x, height);
      context.stroke();
    }
    for (let y = 0; y < height; y += 30) {
      context.beginPath();
      context.moveTo(0, y);
      context.lineTo(width, y);
      context.stroke();
    }

    // Physiological photoplethysmogram / arterial waveform with dicrotic notch
    context.strokeStyle = bpm > 100 ? '#ff6b6b' : (bpm < 60 ? '#feca57' : '#4ecca3');
    context.lineWidth = 2.4;
    context.beginPath();

    for (let x = 0; x < width; x += 2) {
      const cycle = ((x / 75) - simPhase) % 1;
      const t = cycle < 0 ? cycle + 1 : cycle;
      let yNorm = 0;
      if (t < 0.22) {
        // Systolic upstroke & peak
        yNorm = Math.sin((t / 0.22) * Math.PI) * 0.85;
      } else if (t < 0.38) {
        // Dicrotic notch descent
        yNorm = 0.85 - ((t - 0.22) / 0.16) * 0.55;
      } else if (t < 0.52) {
        // Dicrotic secondary rebound wave
        yNorm = 0.30 + Math.sin(((t - 0.38) / 0.14) * Math.PI) * 0.18;
      } else {
        // Diastolic runoff
        yNorm = 0.30 * (1 - (t - 0.52) / 0.48);
      }

      const y = height - (yNorm * (height - 30) + 15);
      if (x === 0) context.moveTo(x, y);
      else context.lineTo(x, y);
    }
    context.stroke();

    simAnimationId = requestAnimationFrame(renderWave);
  }

  simAnimationId = requestAnimationFrame(renderWave);
}

function stopSimulatedCardiacWave() {
  if (simAnimationId) {
    cancelAnimationFrame(simAnimationId);
    simAnimationId = null;
  }
}

if (simNormalBtn) {
  simNormalBtn.addEventListener('click', () => {
    setActiveSimButton(simNormalBtn);
    setPatientCardiacState(
      72,
      'Rhythm: Regular Sinus (Normocardia)',
      'success',
      'Hemodynamic: Stable',
      'Patient Condition: Well Condition (Normal Resting State)',
      'Normal arterial pulse amplitude, regular cycle intervals, and clear dicrotic rebound. All parameters within optimal limits.',
      'Well Condition (Normocardia)',
      'No immediate cardiovascular concerns noted. Maintain routine health screenings.'
    );
    startSimulatedCardiacWave(72);
    if (signalQualityChip) signalQualityChip.innerHTML = 'Signal: <strong>Simulated (72 BPM)</strong>';
    updateMonitorStatus('Simulating normal resting rhythm at 72 BPM with healthy pulse morphology.', 'success');
  });
}

if (simTachyBtn) {
  simTachyBtn.addEventListener('click', () => {
    setActiveSimButton(simTachyBtn);
    setPatientCardiacState(
      112,
      'Rhythm: Sinus Tachycardia (Elevated Rate)',
      'warning',
      'Hemodynamic: Increased Cardiac Output Demand',
      'Patient Condition: Elevated Heart Rate (Tachycardia)',
      'Elevated pulse rate observed (>100 BPM). May correspond to physical exertion, anxiety, fever, dehydration, or stimulant intake.',
      'Tachycardia (Elevated)',
      'Encourage resting comfortably, deep breathing, and hydration. Re-check in 5–10 minutes.'
    );
    startSimulatedCardiacWave(112);
    if (signalQualityChip) signalQualityChip.innerHTML = 'Signal: <strong>Simulated (112 BPM)</strong>';
    updateMonitorStatus('Simulating tachycardia pulse wave at 112 BPM.', 'warning');
  });
}

if (simBradyBtn) {
  simBradyBtn.addEventListener('click', () => {
    setActiveSimButton(simBradyBtn);
    setPatientCardiacState(
      52,
      'Rhythm: Sinus Bradycardia (Low / Athletic Resting)',
      'warning',
      'Hemodynamic: Low Resting Frequency',
      'Patient Condition: Low Pulse Rate (Bradycardia)',
      'Resting heart rate below 60 BPM. Common in endurance athletes or during deep rest; clinical correlation recommended if symptomatic.',
      'Bradycardia (Low Rate)',
      'Evaluate for symptoms such as lightheadedness. In asymptomatic individuals, this often reflects athletic conditioning.'
    );
    startSimulatedCardiacWave(52);
    if (signalQualityChip) signalQualityChip.innerHTML = 'Signal: <strong>Simulated (52 BPM)</strong>';
    updateMonitorStatus('Simulating bradycardia pulse wave at 52 BPM.', 'warning');
  });
}

if (simResetBtn) {
  simResetBtn.addEventListener('click', () => {
    setActiveSimButton(null);
    stopSimulatedCardiacWave();
    setPatientCardiacState(
      null,
      'Rhythm: Awaiting signal',
      'neutral',
      'Hemodynamic: Undetermined',
      'Patient Cardiovascular Health Condition',
      'Center your forehead inside the guide for at least 20 seconds, or select a sample simulation below to evaluate patient condition.',
      'Awaiting Signal',
      'Sit comfortably with forehead well-lit. Avoid talking or rapid head movements during reading.'
    );
    if (signalQualityChip) signalQualityChip.innerHTML = 'Signal: <strong>Idle</strong>';
    updateMonitorStatus('Cardiac monitor reset to idle. Start camera or select a simulation above.', 'neutral');

    if (pulseWaveform) {
      const ctx = pulseWaveform.getContext('2d');
      ctx.clearRect(0, 0, pulseWaveform.width, pulseWaveform.height);
    }
  });
}

function setActiveSimButton(activeBtn) {
  [simNormalBtn, simTachyBtn, simBradyBtn].forEach(btn => {
    if (btn) btn.classList.remove('active');
  });
  if (activeBtn) activeBtn.classList.add('active');
}

/* -------------------------------------------------------------
   Helper Functions
------------------------------------------------------------- */
function updateMonitorStatus(message, tone) {
  if (!monitorStatus) return;
  monitorStatus.className = `result-box ${tone}`;
  monitorStatus.innerHTML = `<h4>Monitoring status</h4><p>${message}</p>`;
}

function updateResult(content, tone, accepted = false) {
  resultBox.className = `result-box ${tone}`;
  resultBox.innerHTML = `<h4>${accepted ? 'Accepted document' : 'Upload status'}</h4><p>${content}</p>`;

  if (accepted) {
    const continueButton = document.createElement('button');
    continueButton.textContent = 'Continue to medical report analysis →';
    continueButton.className = 'primary-btn';
    continueButton.style.marginTop = '10px';
    continueButton.type = 'button';
    continueButton.addEventListener('click', function () {
      try {
        const transfer = new DataTransfer();
        transfer.items.add(fileInput.files[0]);
        reportReaderFileInput.files = transfer.files;
        const readerSection = document.getElementById('report-reader');
        if (readerSection) {
          readerSection.scrollIntoView({ behavior: 'smooth' });
          const panel = readerSection.querySelector('.panel') || readerSection;
          panel.classList.remove('panel-highlight');
          void panel.offsetWidth;
          panel.classList.add('panel-highlight');
        }
        reportReaderForm.requestSubmit();
      } catch (error) {
        updateReaderResult('Please select your validated document again in the Report Reader below.', 'neutral');
        const readerSection = document.getElementById('report-reader');
        if (readerSection) readerSection.scrollIntoView({ behavior: 'smooth' });
      }
    });
    resultBox.appendChild(continueButton);
  }
}

function updateVideoResult(content, tone) {
  videoAnalysisResult.className = `result-box ${tone}`;
  videoAnalysisResult.innerHTML = `<h4>Video analysis status</h4><p>${content}</p>`;
}

function escapeHTML(value) {
  return String(value).replace(/[&<>"']/g, character => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  })[character]);
}

function updateReaderResult(content, tone) {
  reportReaderResultBox.className = `result-box ${tone}`;
  reportReaderResultBox.innerHTML = `<h4>Report extraction status</h4>${content}`;
}

function updateAssistantOutput(content, tone) {
  assistantOutput.className = `result-box ${tone}`;
  assistantOutput.innerHTML = `<h4>Assistant response</h4><p>${escapeHTML(content)}</p>`;
}

// Initialize activity navigation on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  setupActivityNavigation();
});
setupActivityNavigation();
