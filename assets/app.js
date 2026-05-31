/* Catálogo — filtro por origen + búsqueda por código, todo en el navegador.
   No hay backend: opera sobre las tarjetas ya incluidas en el HTML. */

(function () {
  "use strict";

  var grid = document.getElementById("grid");
  var cards = Array.prototype.slice.call(grid.querySelectorAll(".card"));
  var buscador = document.getElementById("buscador");
  var filtros = Array.prototype.slice.call(document.querySelectorAll(".filtro"));
  var conteo = document.getElementById("conteo");
  var vacio = document.getElementById("vacio");

  var origenActivo = "";   // "" = todos
  var consulta = "";

  function aplicar() {
    var visibles = 0;
    var q = consulta.trim().toLowerCase();

    cards.forEach(function (card) {
      var coincideOrigen = !origenActivo || card.dataset.origen === origenActivo;
      var coincideCodigo = !q || card.dataset.codigo.indexOf(q) !== -1;
      var mostrar = coincideOrigen && coincideCodigo;
      card.hidden = !mostrar;
      if (mostrar) visibles++;
    });

    conteo.textContent = visibles + (visibles === 1 ? " producto" : " productos");
    vacio.hidden = visibles !== 0;
  }

  // Búsqueda (con pequeño debounce)
  var t;
  buscador.addEventListener("input", function () {
    consulta = buscador.value;
    clearTimeout(t);
    t = setTimeout(aplicar, 120);
  });

  // Filtros por origen
  filtros.forEach(function (btn) {
    btn.addEventListener("click", function () {
      filtros.forEach(function (b) { b.classList.remove("is-active"); });
      btn.classList.add("is-active");
      origenActivo = btn.dataset.origen || "";
      aplicar();
    });
  });

  // ----- Lightbox / zoom -----
  var lightbox = document.getElementById("lightbox");
  var lbImg = document.getElementById("lightboxImg");
  var lbCaption = document.getElementById("lightboxCaption");
  var lbClose = document.getElementById("lightboxClose");

  function abrirZoom(card) {
    var img = card.querySelector("img");
    var codigo = card.querySelector(".codigo");
    var origen = card.querySelector(".origen");
    var precio = card.dataset.precio;
    lbImg.src = img.src;
    lbImg.alt = img.alt;
    lbCaption.textContent =
      (codigo ? codigo.textContent : "") +
      (origen ? "  ·  " + origen.textContent : "") +
      (precio ? "  ·  " + precio : "");
    lightbox.hidden = false;
    lightbox.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
  }

  function cerrarZoom() {
    lightbox.hidden = true;
    lightbox.setAttribute("aria-hidden", "true");
    lbImg.src = "";
    document.body.style.overflow = "";
  }

  // Abrir al tocar la imagen de cualquier tarjeta (delegación de eventos)
  grid.addEventListener("click", function (e) {
    var imgWrap = e.target.closest(".card-img");
    if (!imgWrap) return;
    var card = imgWrap.closest(".card");
    if (card) abrirZoom(card);
  });

  lightbox.addEventListener("click", cerrarZoom);
  lbClose.addEventListener("click", cerrarZoom);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !lightbox.hidden) cerrarZoom();
  });

  aplicar();
})();
