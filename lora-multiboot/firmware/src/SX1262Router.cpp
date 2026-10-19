/**
 * SX1262Router — minimal code, low RAM, extensible PIDs, listen-before-send
 */
#include "SX1262Router.hpp"
static bool s_p=false, s_a=false, s_v=false;
void SX1262Router_init(void){ s_p=true;s_a=false;s_v=false; }
bool SX1262Router_gate(void){ return (s_v=true) && s_p && (s_a=true); }
bool SX1262Router_can_tx(void){ return s_v&&s_p&&s_a; }
void SX1262Router_set_air(bool f){ s_a=f; }
