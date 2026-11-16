$(function () {
    $(".tabla-datos").DataTable({
        pageLength: 5,
        lengthMenu: [5, 10, 25],
        order: [],
        columnDefs: [{ targets: "sin-orden", orderable: false, searchable: false }],
        language: {
            search: "Buscar:",
            lengthMenu: "Mostrar _MENU_ filas",
            info: "_START_–_END_ de _TOTAL_ registros",
            infoEmpty: "0 registros",
            infoFiltered: "(de _MAX_ registros)",
            zeroRecords: "Sin coincidencias",
            emptyTable: "Todavía no hay registros",
            paginate: { previous: "Anterior", next: "Siguiente" },
            aria: { sortAscending: ": ordenar ascendente", sortDescending: ": ordenar descendente" }
        }
    });
});
