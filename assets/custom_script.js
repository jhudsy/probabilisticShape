
document.addEventListener('keydown', function (event) {
    // Check if the target is an input field
    if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
        return;
    }

    // Backspace (8) or Delete (46)
    if (event.keyCode === 8 || event.keyCode === 46) {
        var deleteBtn = document.getElementById('btn-delete');
        if (deleteBtn) {
            deleteBtn.click();
            event.preventDefault(); // Prevent browser back navigation
        }
    }
});
