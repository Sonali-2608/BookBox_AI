import { motion } from "framer-motion";

// Explicit pixel layout (rather than flexbox) so the connector-line SVG
// coordinates below can line up with each spine's top edge precisely.
const SPINES = [
  { left: 12, height: 190, rotate: -14, color: "#9C7A3E", title: "Atomic Habits" },
  { left: 62, height: 232, rotate: -8, color: "#3F6355", title: "Deep Work" },
  { left: 112, height: 258, rotate: -2, color: "#2E3B63", title: "Sapiens" },
  { left: 162, height: 240, rotate: 4, color: "#2C4A3F", title: "The Hobbit" },
  { left: 212, height: 206, rotate: 10, color: "#4A3B63", title: "Educated" },
  { left: 262, height: 224, rotate: 16, color: "#C9A15C", title: "Circe" },
];

const CONTAINER_H = 320;
const SPINE_W = 34;

function topPoint(spine) {
  return { x: spine.left + SPINE_W / 2, y: CONTAINER_H - spine.height };
}

const links = [
  [SPINES[0], SPINES[2]],
  [SPINES[2], SPINES[4]],
];

export default function HeroShelf() {
  return (
    <div
      className="relative mx-auto"
      style={{ width: 320, height: CONTAINER_H }}
      aria-hidden="true"
    >
      <svg
        className="pointer-events-none absolute inset-0"
        width={320}
        height={CONTAINER_H}
        viewBox={`0 0 320 ${CONTAINER_H}`}
      >
        {links.map(([a, b], i) => {
          const p1 = topPoint(a);
          const p2 = topPoint(b);
          const midX = (p1.x + p2.x) / 2;
          const d = `M${p1.x},${p1.y} Q${midX},${Math.min(p1.y, p2.y) - 50} ${p2.x},${p2.y}`;
          return (
            <g key={i}>
              <motion.path
                d={d}
                fill="none"
                stroke="#C9A15C"
                strokeWidth={1.25}
                strokeDasharray="4 4"
                initial={{ pathLength: 0, opacity: 0 }}
                whileInView={{ pathLength: 1, opacity: 0.7 }}
                viewport={{ once: true }}
                transition={{ duration: 1.1, delay: 0.4 + i * 0.3, ease: "easeInOut" }}
              />
              <motion.circle
                cx={p1.x}
                cy={p1.y}
                r={2.5}
                fill="#E3C588"
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                viewport={{ once: true }}
                transition={{ delay: 0.4 + i * 0.3 }}
              />
              <motion.circle
                cx={p2.x}
                cy={p2.y}
                r={2.5}
                fill="#E3C588"
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                viewport={{ once: true }}
                transition={{ delay: 0.4 + i * 0.3 + 0.3 }}
              />
            </g>
          );
        })}
      </svg>

      {SPINES.map((spine, i) => (
        <motion.div
          key={spine.title}
          initial={{ y: 40, opacity: 0 }}
          whileInView={{ y: 0, opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: i * 0.08, ease: "easeOut" }}
          className="absolute bottom-0 flex items-end justify-center rounded-t-sm rounded-b-[2px] shadow-card-dark"
          style={{
            left: spine.left,
            width: SPINE_W,
            height: spine.height,
            backgroundColor: spine.color,
            transformOrigin: "bottom center",
            rotate: `${spine.rotate}deg`,
          }}
        >
          <span
            className="mb-3 font-mono text-[10px] uppercase tracking-wider text-parchment/80"
            style={{ writingMode: "vertical-rl", transform: "rotate(180deg)" }}
          >
            {spine.title}
          </span>
        </motion.div>
      ))}
    </div>
  );
}
