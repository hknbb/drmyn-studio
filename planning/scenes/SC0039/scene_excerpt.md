# SC0039 Scene Excerpt

- Source file: `source/screenplay/closing_price.fountain`
- Source lines: `3011-3087`
- Retrieval map: `planning/manifests/closing_price_scene_retrieval_map.json`
- Boundary: `slug -> slug`
- Scene text SHA256: `2f2e6039141910567dac895e7b806f5d91d8f90747a02e6b5881d601de7f8bd1`

```fountain
INT. SERVICE UTILITY SPACE — MARKET DISTRICT SUBSTRUCTURE — NIGHT

A maintenance corridor beneath one of the market district's older blocks — a service passage that has not been used for actual maintenance in some years. A locked door with a broken lock, the kind that reads as locked from outside and is not. Pipes. A junction box. The particular silence of a space no one is supposed to be in.

NADIA works by the light of a single device — low output, angled down, nothing visible from the passage door. She has laid out what she has: a modified relay node, two mesh adapters with separate protocol stacks, a physical cipher card she has not used in eight months.

She starts with the relay node. Standard channel, second-tier network, the kind of routing that civilian infrastructure uses so extensively that professional surveillance has to make choices about what to prioritize.

She initiates a handshake.

The response takes 340 milliseconds. It should take 210.

She closes the connection.

The latency signature is wrong. Not wrong in the way of a failing network — wrong in the way of a network that has been optimized for something other than what it is presenting as. The response packet arrived too smoothly. Clean. Someone has been through this route and improved it, which is not something that happens in unmaintained civilian infrastructure unless there is a reason.

She moves to the mesh adapters. Secondary protocol, different network layer, the kind of path that requires knowing it exists before you can surveil it.

She runs the first adapter for thirty seconds and watches the traffic shape.

It is the wrong shape.

Not wrong in an obvious way. Wrong in the specific way that she has seen before — the packet distribution follows a slightly too-regular interval, the kind of regularity that is a byproduct of interception architecture that normalizes timing to avoid detection. She has seen this signature exactly once before, in a different city, under a different operation. She knows what it is.

She pulls the adapter.

The encrypted courier protocol takes four minutes to initiate. She gives it the time. The protocol uses a distributed handshake across seven nodes; compromise of the route would require controlling at least four of them.

She watches the handshake proceed.

Node one: clean. Node two: clean. Node three: clean. Node four — the timing delta is wrong. Off by eleven milliseconds, which is nothing, except that eleven milliseconds is exactly the overhead introduced by a passive intercept relay inserted into a node's traffic flow.

She aborts the handshake at node five.

The physical drop point. She seeded it eighteen months ago, before the operation she is now inside started. A dead-drop relay registered under a cover identity in a secondary communications registry — the kind of thing that requires knowing the registry exists. It is not surveillance-obvious. It should not be in anyone's systematic coverage.

She runs the activation sequence.

The registry responds.

The response is correct in every detail. The cipher validates. The timing is right.

She holds the connection open for six seconds and reads the traffic shape underneath the response.

There is traffic underneath the response. There should not be.

She closes the connection.

She sets the hardware down. She looks at the junction box across the passage — not looking at it, using it as a fixed point for thinking.

Every channel she knows to use has been covered. Not clumsily. Not with obvious surveillance — no failed connections, no error signatures, nothing that would have been detectable on a first-pass check. Someone has gone through the infrastructure she would know to reach for and made it look undisturbed. This is patient work. This is the work of someone who understood the categories and covered them.

She knows the shape of this kind of work. She has read about it in briefings she was not supposed to retain. Institutional routing. No fingerprints. The kind of coverage that doesn't declare itself as surveillance; it simply makes every path lead somewhere it shouldn't.

Agent Sable.

She does not know Sable's name. She knows the signature.

She stays with the junction box for another moment.

She has one option she has not tried. It is not an option she would have considered in normal operating conditions. A media contact — not a professional contact, not someone in her network, barely a name. An investigative journalist whose byline she has seen twice in the last year on pieces that came too close to Roman's network for coincidence. Someone working a story from the outside. Someone who would not be in Sable's systematic coverage because Sable's coverage is built for professional channels — encrypted networks, courier protocols, counter-surveillance infrastructure.

A journalist would use civilian infrastructure. Open channels. The kind of thing that is hard to surveil precisely because it is so easy to surveil that it blends with noise.

She tries to reconstruct the name.

Seraphina — something. Mast, possibly. She has seen the byline twice and remembered it for the wrong reasons: the first piece came too close to the Rennmark numbers, the second piece described a courier network that she recognized as adjacent to Roman's distribution architecture.

She is not a contact. She is a name on two pieces of journalism that Nadia read and filed and did not expect to need.

Reaching her is not safe. Reaching her means surfacing in a channel that Nadia cannot evaluate, through a civilian infrastructure she does not control, to a person whose reliability she has no basis to assess.

It is what remains.

She records the name — partial, uncertain — and closes the device down. The service passage returns to its proper dark.

She has until the odds run out.
```
