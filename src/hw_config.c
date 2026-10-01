/* hw_config.c
Copyright 2021 Carl John Kugler III

Licensed under the Apache License, Version 2.0 (the License); you may not use
this file except in compliance with the License. You may obtain a copy of the
License at

   http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an AS IS BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
*/

#include "hw_config.h"

#ifdef SB_SD_SDIO
/* SDIO Interface Configuration 
 * Pin mapping details for your requested GPIO 12-18 range:
 * CLK = 12 (Derived automatically by the PIO logic as D0_gpio - 2)
 * CMD = 13
 * D0  = 14
 * D1  = 15
 * D2  = 16
 * D3  = 17
 */
static sd_sdio_if_t sdio_if = {
    .CMD_gpio = 13,
    .D0_gpio = 14,
    .baud_rate = 8 * 1000000 // 8 MHz
};

/* Hardware Configuration of the SD Card socket "object" */
static sd_card_t sd_card = {
    .type = SD_IF_SDIO, 
    .sdio_if_p = &sdio_if,
    .use_card_detect = false,
    // .card_detect_gpio = 18, // Uncomment if you want to use GPIO 18 for Card Detect
    // .card_detected_true = 0
};
#else
/* SPI Interface Configuration (StereoMag dev kit cartridge)
 * The cartridge wires the microSD socket to SPI1, shared with the VS1053:
 * SCK = 30, TX/MOSI = 31, RX/MISO = 28, CS = 2 (SD_CS on the cartridge port)
 *
 * The bus is left at the SD baud rate after each card access, and the VS1053
 * driver does not set its own rate, so stay below the VS1053's SCI read limit
 * (CLKI/7 = ~6.8 MHz with SCI_CLOCKF = 0xB000 and a 12 MHz crystal).
 */
static spi_t spi = {
    .hw_inst = spi1,
    .sck_gpio = 30,
    .mosi_gpio = 31,
    .miso_gpio = 28,
    .baud_rate = 6 * 1000000 // 6 MHz
};

static sd_spi_if_t spi_if = {
    .spi = &spi,
    .ss_gpio = 2
};

/* Hardware Configuration of the SD Card socket "object" */
static sd_card_t sd_card = {
    .type = SD_IF_SPI,
    .spi_if_p = &spi_if,
    .use_card_detect = false,
    // .card_detect_gpio = 41, // SD_DETECT on the cartridge port; polarity depends on the socket
    // .card_detected_true = 0
};
#endif

/* ********************************************************************** */

size_t sd_get_num() { return 1; }

/**
 * @brief Get a pointer to an SD card object by its number.
 *
 * @param[in] num The number of the SD card to get.
 *
 * @return A pointer to the SD card object, or @c NULL if the number is invalid.
 */
sd_card_t* sd_get_by_num(size_t num) {
    if (0 == num) {
        return &sd_card;
    } else {
        return NULL;
    }
}

/* [] END OF FILE */