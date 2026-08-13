import { motion } from "framer-motion";

export default function FeatureCard({ icon: Icon, callNumber, title, description, index = 0 }) {
  return (
    <motion.div
      initial={{ y: 24, opacity: 0 }}
      whileInView={{ y: 0, opacity: 1 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.5, delay: index * 0.08 }}
      className="catalog-card p-6"
    >
      <div className="flex items-center justify-between">
        <span className="call-number">{callNumber}</span>
        <Icon className="h-5 w-5 text-moss-dark/70" strokeWidth={1.75} />
      </div>
      <h3 className="mt-4 font-display text-xl font-medium text-parchment-ink">{title}</h3>
      <div className="catalog-card__rule" />
      <p className="mt-3 text-sm leading-relaxed text-parchment-ink/70">{description}</p>
    </motion.div>
  );
}
