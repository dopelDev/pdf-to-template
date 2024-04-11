// Lista negra con los elementos en minúsculas
const blacklist = ["ppp reduction", "total wage", "n / a"];

// Función para verificar si un texto está en la lista negra
function isBlacklisted(text) {
    const lowerText = text.toLowerCase();
    return blacklist.some(blacklistItem => lowerText.includes(blacklistItem));
}

// Función para convertir un string de moneda a float
function convertirMonedaAFloat(valorString) {
    const numero = parseFloat(valorString.replace(/[$,]/g, '').trim());
    return isNaN(numero) ? 0 : numero;
}

function colorearTextoCeldasERC2020() {
    document.querySelectorAll('table').forEach(tabla => {
        tabla.querySelectorAll('tbody tr').forEach(fila => {
            // Asumiendo que el nombre del empleado está en la primera celda (índice 0)
            const nombreEmpleado = fila.cells[0].textContent.trim();
            
            // Verifica si el nombre del empleado está en la lista negra y omite la fila si es así
            if (isBlacklisted(nombreEmpleado)) {
                return; // Continúa con la siguiente fila
            }

            const posicionesERC2020 = [6, 9, 12];
            posicionesERC2020.forEach(posicion => {
                const celdaERC = fila.cells[posicion];
                if (celdaERC) { // No es necesario verificar la lista negra aquí nuevamente
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
            // Asumiendo que el nombre del empleado está en la primera celda (índice 0)
            const nombreEmpleado = fila.cells[0].textContent.trim();
            
            // Verifica si el nombre del empleado está en la lista negra y omite la fila si es así
            if (isBlacklisted(nombreEmpleado)) {
                return; // Continúa con la siguiente fila
            }

            const posicionesERC2021 = [15, 18, 21];
            const posicionTotal = 22;
            let sumaERC = 0;

            posicionesERC2021.forEach(posicion => {
                const celdaERC = fila.cells[posicion];
                const valor = convertirMonedaAFloat(celdaERC.textContent);
                sumaERC += valor;
                if (valor < 7000) {
                    celdaERC.style.color = 'green';
                } else {
                    celdaERC.style.backgroundColor = 'red';
                    celdaERC.style.color = 'white';
                }
            });

            const celdaTotal = fila.cells[posicionTotal];
            if (celdaTotal && sumaERC >= 21000) {
                celdaTotal.style.backgroundColor = 'red';
                celdaTotal.style.color = 'white';
            }
        });
    });
}


// Agregar el evento para ejecutar las funciones una vez que el contenido del DOM esté cargado
document.addEventListener('DOMContentLoaded', () => {
    colorearTextoCeldasERC2020();
    colorearCeldasERC2021();
});

