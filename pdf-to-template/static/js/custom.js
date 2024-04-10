// Función para convertir un string de moneda a float
function convertirMonedaAFloat(valorString) {
    // Reemplaza el símbolo del dólar ($) y las comas (,) antes de convertir el string a float
    const numero = parseFloat(valorString.replace(/[$,]/g, '').trim());
    return isNaN(numero) ? 0 : numero;
}
function colorearTextoCeldasERC2020() {
    document.querySelectorAll('table').forEach(tabla => {
        tabla.querySelectorAll('tbody tr').forEach(fila => {
            const posicionesERC2020 = [6, 9, 12];
            posicionesERC2020.forEach(posicion => {
                const celdaERC = fila.cells[posicion];
                if (celdaERC) {
                    const valor = convertirMonedaAFloat(celdaERC.textContent);
                    if (valor > 5000) {
                        celdaERC.style.backgroundColor = 'red';
                        celdaERC.style.color = 'white';
                    } else {
                        celdaERC.style.color = 'green';
                    }
                }
            });
        });
    });
}

function colorearCeldasERC2021() {
    document.querySelectorAll('table').forEach(tabla => {
        tabla.querySelectorAll('tbody tr').forEach(fila => {
            const posicionesERC2021 = [15, 18, 21];
            const posicionTotal = 22;
            let sumaERC = 0;

            posicionesERC2021.forEach(posicion => {
                const celdaERC = fila.cells[posicion];
                if (celdaERC) {
                    const valor = convertirMonedaAFloat(celdaERC.textContent);
                    sumaERC += valor;
                    if (valor < 7000) {
                        celdaERC.style.color = 'green';
                    } else {
                        celdaERC.style.backgroundColor = 'red';
                        celdaERC.style.color = 'white';
                    }
                }
            });

            const celdaTotal = fila.cells[posicionTotal];
            if (celdaTotal) {
                const valorTotal = convertirMonedaAFloat(celdaTotal.textContent);
                if (valorTotal >= 21000) {
                    celdaTotal.style.backgroundColor = 'red';
                    celdaTotal.style.color = 'white';
                }
            }
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    colorearTextoCeldasERC2020(); // Función para ERC Credit de 2020
    colorearCeldasERC2021(); // Función para ERC Credit de 2021
});
