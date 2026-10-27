#ifndef EIGHTBITDO_RECEIVER_BOARD_PINS_H
#define EIGHTBITDO_RECEIVER_BOARD_PINS_H

#include <stdbool.h>
#include <stdint.h>

/*
 * 8BitDo receiver, GD32F103C8T6 / LQFP48, supplied v2.04 and v2.05.
 * Button: PA1, physical pin 11, active low with internal pull-up.
 * RGB: mask 1 -> PB9/pin46, mask 2 -> PB8/pin45, mask 4 -> PB5/pin41.
 * All three LED channels are active low. Physical R/G/B order is unverified;
 * channel numbers reproduce the firmware's masks without assuming colors.
 * HCI: PA2/pin12 TX -> radio RX; PA3/pin13 RX <- radio TX.
 *
 * Call board_gpio_init() from your own firmware after runtime startup.
 * Only the button and three LED GPIOs are configured here. Clock-tree,
 * UART, Bluetooth bring-up, vector-table/linker setup and debounce are
 * outside this helper. Ordinary GPIO use needs no AFIO remapping.
 */
#define EBD_MMIO32(address) (*(volatile uint32_t *)(uintptr_t)(address))
#define EBD_RCU_APB2EN      EBD_MMIO32(0x40021018u)
#define EBD_GPIOA_CTL0      EBD_MMIO32(0x40010800u)
#define EBD_GPIOA_ISTAT     EBD_MMIO32(0x40010808u)
#define EBD_GPIOA_BOP       EBD_MMIO32(0x40010810u)
#define EBD_GPIOB_CTL0      EBD_MMIO32(0x40010C00u)
#define EBD_GPIOB_CTL1      EBD_MMIO32(0x40010C04u)
#define EBD_GPIOB_BOP       EBD_MMIO32(0x40010C10u)
#define EBD_BUTTON_MASK    (1u << 1)
#define EBD_LED_PB9_MASK    (1u << 9)
#define EBD_LED_PB8_MASK    (1u << 8)
#define EBD_LED_PB5_MASK    (1u << 5)
#define EBD_LED_ALL_PINS    (EBD_LED_PB9_MASK | EBD_LED_PB8_MASK | EBD_LED_PB5_MASK)
#define EBD_LED_CH1        0x01u /* PB9 / package pin 46 */
#define EBD_LED_CH2        0x02u /* PB8 / package pin 45 */
#define EBD_LED_CH4        0x04u /* PB5 / package pin 41 */

/* Reference constants only: these do not initialize or drive the radio. */
#define EBD_HCI_USART_BASE  0x40004400u /* GD32 USART1; STM32 naming USART2 */
#define EBD_HCI_TX_PA2_MASK (1u << 2)
#define EBD_HCI_RX_PA3_MASK (1u << 3)
#define EBD_HCI_START_BAUD  115200u
#define EBD_HCI_RUN_BAUD    1500000u
#define EBD_RADIO_CTRL_PB13 (1u << 13) /* Low/high startup control; likely LDO_ON */
#define EBD_RADIO_SCL_PB10  (1u << 10)
#define EBD_RADIO_SDA_PB11  (1u << 11)

static inline void board_gpio_init(void)
{
    EBD_RCU_APB2EN |= (1u << 2) | (1u << 3); /* GPIOA and GPIOB clocks */
    (void)EBD_RCU_APB2EN;

    /* PA1 input mode nibble 8; output latch high selects the pull-up. */
    EBD_GPIOA_BOP = EBD_BUTTON_MASK;
    EBD_GPIOA_CTL0 = (EBD_GPIOA_CTL0 & ~(0xFu << 4)) | (0x8u << 4);

    /* Preload all three high = off before enabling push-pull / 10 MHz. */
    EBD_GPIOB_BOP = EBD_LED_ALL_PINS;
    EBD_GPIOB_CTL0 = (EBD_GPIOB_CTL0 & ~(0xFu << 20)) | (0x1u << 20);
    EBD_GPIOB_CTL1 = (EBD_GPIOB_CTL1 & ~0xFFu) | 0x11u; /* PB8 and PB9 */
}

static inline bool board_button_pressed(void)
{
    return (EBD_GPIOA_ISTAT & EBD_BUTTON_MASK) == 0u;
}

static inline void board_led_channels_set(uint8_t channels_on)
{
    uint32_t low = 0u;
    if ((channels_on & EBD_LED_CH1) != 0u) low |= EBD_LED_PB9_MASK;
    if ((channels_on & EBD_LED_CH2) != 0u) low |= EBD_LED_PB8_MASK;
    if ((channels_on & EBD_LED_CH4) != 0u) low |= EBD_LED_PB5_MASK;
    /* One atomic write: low-half sets off pins; high-half clears on pins. */
    EBD_GPIOB_BOP = (EBD_LED_ALL_PINS & ~low) | (low << 16);
}

#endif
