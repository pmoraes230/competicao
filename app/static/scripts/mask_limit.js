const limit_peaple = document.getElementById('peaple_limit');

limit_peaple.addEventListener('input', function(e) {
    let value = e.target.value.replace(/\D/g, '')
    e.target.value = value;
})