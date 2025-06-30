document.addEventListener('DOMContentLoaded', function() {
    const limit_peaple = document.getElementById('peaple_limit');
    const limit_seats = document.getElementById('limit_seats');
    
    const handleInput = (e) => {
        let value = e.target.value.replace(/\D/g, '');
        e.target.value = value
    }
    
    [limit_peaple, limit_seats].forEach(element => {
        if(element){
            element.addEventListener('input', handleInput)
        }
    })
})