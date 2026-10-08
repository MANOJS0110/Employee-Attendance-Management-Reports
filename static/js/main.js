/**
 * Enterprise Employee Attendance & Workforce System - Core Client JS
 */

// Live Digital Clock
function initLiveClock() {
    const clockEl = document.getElementById('liveDigitalClock');
    if (!clockEl) return;

    function update() {
        const now = new Date();
        let hours = now.getHours();
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        const ampm = hours >= 12 ? 'PM' : 'AM';
        hours = hours % 12;
        hours = hours ? hours : 12; // 0 becomes 12
        const strTime = `${String(hours).padStart(2, '0')}:${minutes}:${seconds} ${ampm}`;
        clockEl.textContent = strTime;
    }
    update();
    setInterval(update, 1000);
}

// Check-In Action
async function handleCheckIn() {
    const btn = document.getElementById('btnCheckIn');
    if (btn) btn.disabled = true;

    try {
        const res = await fetch('/api/attendance/check-in', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ remarks: 'Punched via Web Portal' })
        });
        const data = await res.json();

        if (data.success) {
            Swal.fire({
                icon: 'success',
                title: 'Check-In Successful!',
                text: `${data.message}`,
                confirmButtonColor: '#1B365D'
            }).then(() => {
                window.location.reload();
            });
        } else {
            Swal.fire({
                icon: 'warning',
                title: 'Check-In Notice',
                text: data.message,
                confirmButtonColor: '#1B365D'
            });
            if (btn) btn.disabled = false;
        }
    } catch (err) {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Failed to record check-in. Please try again.',
            confirmButtonColor: '#1B365D'
        });
        if (btn) btn.disabled = false;
    }
}

// Check-Out Action
async function handleCheckOut() {
    const btn = document.getElementById('btnCheckOut');
    if (btn) btn.disabled = true;

    try {
        const res = await fetch('/api/attendance/check-out', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ remarks: 'Shift Completed' })
        });
        const data = await res.json();

        if (data.success) {
            Swal.fire({
                icon: 'success',
                title: 'Check-Out Recorded!',
                text: `${data.message}`,
                confirmButtonColor: '#1B365D'
            }).then(() => {
                window.location.reload();
            });
        } else {
            Swal.fire({
                icon: 'warning',
                title: 'Check-Out Notice',
                text: data.message,
                confirmButtonColor: '#1B365D'
            });
            if (btn) btn.disabled = false;
        }
    } catch (err) {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Failed to record check-out. Please try again.',
            confirmButtonColor: '#1B365D'
        });
        if (btn) btn.disabled = false;
    }
}

// Submit Leave Application
async function submitLeaveApplication(event) {
    event.preventDefault();
    const form = document.getElementById('leaveApplyForm');
    const formData = new FormData(form);

    const payload = {
        leave_type: formData.get('leave_type'),
        start_date: formData.get('start_date'),
        end_date: formData.get('end_date'),
        reason: formData.get('reason')
    };

    try {
        const res = await fetch('/api/leaves/apply', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (data.success) {
            Swal.fire({
                icon: 'success',
                title: 'Leave Submitted!',
                text: data.message,
                confirmButtonColor: '#1B365D'
            }).then(() => {
                window.location.reload();
            });
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Submission Failed',
                text: data.message,
                confirmButtonColor: '#1B365D'
            });
        }
    } catch (err) {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'An error occurred while submitting your leave application.',
            confirmButtonColor: '#1B365D'
        });
    }
}

// Approve Leave Request (HR / Admin)
async function approveLeave(leaveId) {
    const { value: remarks } = await Swal.fire({
        title: 'Approve Leave Request',
        input: 'text',
        inputLabel: 'Manager / HR Approval Remarks (Optional):',
        inputValue: 'Approved as per company leave guidelines',
        showCancelButton: true,
        confirmButtonColor: '#10B981',
        cancelButtonColor: '#6B7280',
        confirmButtonText: 'Confirm Approval'
    });

    if (remarks !== undefined) {
        try {
            const res = await fetch(`/api/leaves/${leaveId}/approve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ remarks })
            });
            const data = await res.json();

            if (data.success) {
                Swal.fire('Approved!', data.message, 'success').then(() => {
                    window.location.reload();
                });
            } else {
                Swal.fire('Error', data.message, 'error');
            }
        } catch (err) {
            Swal.fire('Error', 'Failed to approve request', 'error');
        }
    }
}

// Reject Leave Request (HR / Admin)
async function rejectLeave(leaveId) {
    const { value: remarks } = await Swal.fire({
        title: 'Reject Leave Request',
        input: 'text',
        inputLabel: 'Rejection Reason:',
        inputPlaceholder: 'e.g. Critical project deadline / Insufficient coverage',
        showCancelButton: true,
        confirmButtonColor: '#EF4444',
        cancelButtonColor: '#6B7280',
        confirmButtonText: 'Confirm Rejection',
        inputValidator: (value) => {
            if (!value) {
                return 'Please provide a reason for rejection!';
            }
        }
    });

    if (remarks) {
        try {
            const res = await fetch(`/api/leaves/${leaveId}/reject`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ remarks })
            });
            const data = await res.json();

            if (data.success) {
                Swal.fire('Rejected', data.message, 'info').then(() => {
                    window.location.reload();
                });
            } else {
                Swal.fire('Error', data.message, 'error');
            }
        } catch (err) {
            Swal.fire('Error', 'Failed to reject request', 'error');
        }
    }
}

// Trigger Batch Absent Job
async function triggerBatchAbsent() {
    const confirm = await Swal.fire({
        title: 'Run End-of-Day Absent Marker?',
        text: 'This automated batch process identifies all active employees without attendance today (and not on approved leave) and records them as ABSENT.',
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#1B365D',
        cancelButtonColor: '#6B7280',
        confirmButtonText: 'Yes, Execute Now'
    });

    if (confirm.isConfirmed) {
        try {
            const res = await fetch('/api/attendance/batch-absent', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await res.json();
            if (data.success) {
                Swal.fire('Job Completed!', data.message, 'success').then(() => {
                    window.location.reload();
                });
            } else {
                Swal.fire('Notice', data.message, 'info');
            }
        } catch (err) {
            Swal.fire('Error', 'Failed to run batch absent process', 'error');
        }
    }
}

// Trigger Power BI Dataset Refresh
async function syncPowerBIDatasets() {
    try {
        const res = await fetch('/api/powerbi/export-sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        if (data.success) {
            Swal.fire('Power BI Synced!', data.message, 'success');
        } else {
            Swal.fire('Error', data.message, 'error');
        }
    } catch (err) {
        Swal.fire('Error', 'Failed to sync Power BI datasets', 'error');
    }
}

// Copy Code to Clipboard
function copyToClipboard(button, codeId) {
    const codeElement = document.getElementById(codeId);
    if (!codeElement) return;

    navigator.clipboard.writeText(codeElement.innerText).then(() => {
        const origText = button.innerHTML;
        button.innerHTML = '<i class="bi bi-check-lg"></i> Copied!';
        button.classList.remove('btn-outline-light');
        button.classList.add('btn-success');
        setTimeout(() => {
            button.innerHTML = origText;
            button.classList.remove('btn-success');
            button.classList.add('btn-outline-light');
        }, 2000);
    });
}

// DOM Ready
document.addEventListener('DOMContentLoaded', () => {
    initLiveClock();
});
