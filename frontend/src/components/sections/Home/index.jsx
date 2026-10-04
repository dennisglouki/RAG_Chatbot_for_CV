import { motion } from 'framer-motion'
import { Terminal } from 'lucide-react'
import { ChatBox } from './ChatBox'
import { IntroSection } from './IntroSection'
import { getPersonalInfo } from '../../../config/configLoader'

export const HomeSection = () => {
  const personalInfo = getPersonalInfo();
  
  return (
    <motion.div
      key="home"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
      className="min-h-[calc(100vh-6rem)] flex flex-col items-center justify-center text-center"
    >
      <motion.div 
        className="mb-4 relative"
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", bounce: 0.5 }}
      >
        <div className="w-40 h-40 md:w-43 md:h-43 rounded-full overflow-hidden border-4 border-purple-500 relative">
          <img 
            src="/profile.jpg" 
            alt={personalInfo.name}
            className="w-full h-full object-cover object-[50%_17%] scale-[1.8]"
          />
          <div className="absolute inset-0 bg-gradient-to-br from-purple-500/20 to-transparent" />
        </div>
        <motion.div 
          className="absolute -bottom-0 -right-2 w-9 h-9 md:w-9 m9:h-9 bg-purple-500 rounded-full flex items-center justify-center"
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
        >
          <Terminal className="w-5 h-5 md:w-6 md:h-6 text-white" />
        </motion.div>
      </motion.div>

      <motion.h1
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4 }}
        className="text-4xl md:text-5xl font-bold mb-2 bg-gradient-to-r from-purple-400 to-pink-600 bg-clip-text text-transparent leading-relaxed px-4 py-1"
      >
        {personalInfo.name}
      </motion.h1>


      
      {/* <IntroSection /> */}

<motion.p
  initial={{ opacity: 0, y: 10 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.4, delay: 0.2 }}
  className="relative z-50 w-full max-w-4xl mx-auto px-6 mb-6 text-left text-sm md:text-base text-gray-400 leading-relaxed"
>
  I'm a Business & Data Analyst combining expertise in Analytics,
  Psychology, and Finance with a passion for data, technology, and AI.
  I enjoy building data-driven solutions that connect technical
  possibilities with real-world business needs.{" "}

  <a
    href="https://dennisg.onrender.com/CV_Dennis_Gloukhman.pdf"
    target="_blank"
    rel="noopener noreferrer"
    className="relative z-50 inline-block text-gray-400 hover:text-blue-400  transition-colors underline cursor-pointer"
  >
    Explore my CV!
  </a>
</motion.p>
      <ChatBox />

    </motion.div>
  )
} 