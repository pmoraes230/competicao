function updateTotalPrice() {
    const unitPrice = '{{ event.preco_evento|floatformat:2 }}';
    const quantity = document.getElementById('quantidade').value;
    const totalPrice = unitPrice * quantity;
    document.getElementById('total-price').innerText = `Preço total: R$ ${totalPrice.toFixed(2)}`;
}
