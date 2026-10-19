#ifndef SX1262ROUTER_HPP
#define SX1262ROUTER_HPP
#include <stdbool.h>

void SX1262Router_init(void);
bool SX1262Router_gate(void);      // validate + listen (combined, shorter code)
bool SX1262Router_can_tx(void);
void SX1262Router_set_air(bool f);

#endif
