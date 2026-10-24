/**
 * Food Ordering and Restaurant Management System
 * Interactive client-side scripts
 * Clean, readable, and easy to explain for project viva!
 */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Order Type Selection (DineIn vs TakeAway)
  const dineInRadio = document.getElementById('order_type_dinein');
  const takeAwayRadio = document.getElementById('order_type_takeaway');
  const tableGroup = document.getElementById('table_selection_group');
  const dineInCard = document.getElementById('card_type_dinein');
  const takeAwayCard = document.getElementById('card_type_takeaway');

  function updateOrderType() {
    if (dineInRadio && takeAwayRadio) {
      if (dineInRadio.checked) {
        if (tableGroup) tableGroup.style.display = 'block';
        if (dineInCard) dineInCard.classList.add('selected');
        if (takeAwayCard) takeAwayCard.classList.remove('selected');
      } else {
        if (tableGroup) tableGroup.style.display = 'none';
        if (takeAwayCard) takeAwayCard.classList.add('selected');
        if (dineInCard) dineInCard.classList.remove('selected');
      }
    }
  }

  if (dineInRadio && takeAwayRadio) {
    dineInRadio.addEventListener('change', updateOrderType);
    takeAwayRadio.addEventListener('change', updateOrderType);
    updateOrderType(); // initialize on load
  }

  // 2. Click-to-apply coupon helper
  window.applyCouponCode = function (code) {
    const couponInput = document.getElementById('coupon_input');
    if (couponInput) {
      couponInput.value = code;
      const form = couponInput.closest('form');
      if (form) form.submit();
    } else {
      // If on offers page, copy to clipboard and notify
      navigator.clipboard.writeText(code).then(() => {
        alert('Coupon code "' + code + '" copied to clipboard! Paste it at checkout.');
      });
    }
  };

  // 3. Auto-dismiss alerts after 5 seconds
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.5s ease';
      alert.style.opacity = '0';
      setTimeout(() => alert.remove(), 500);
    }, 5000);
  });
});
