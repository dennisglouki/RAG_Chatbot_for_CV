import { motion } from 'framer-motion'
import { Github, ExternalLink, BookOpen, FileText } from 'lucide-react'
import { useGithubRepos } from '../../../hooks/useGithubRepos'

const ResearchTile = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="group relative min-h-[200px] flex w-full"
    >
      <div className="absolute inset-0 bg-gradient-to-br from-blue-500/20 to-transparent rounded-lg transform group-hover:scale-105 transition-transform" />

      <div className="relative p-4 md:p-6 rounded-lg bg-white/5 border border-white/10 backdrop-blur-sm w-full flex flex-col">

        
        <h3 className="text-xl font-bold mb-2">
          Automation of Literature Screening for Meta-Analyses
        </h3>
        <div className="flex items-center gap-2 mb-3 text-blue-400">
          <BookOpen className="w-5 h-5" />
          <span className="text-sm">Research Publication</span>
        </div>


        <p className="text-gray-400 mb-4 line-clamp-3">
          Evaluation of text-mining approaches for facilitating the screening
          and selection of studies in psychology meta-analyses.
        </p>

        <div className="mt-auto">
          <a
            href="https://link.springer.com/article/10.1186/s13643-026-03275-x"
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 rounded-lg bg-blue-500 hover:bg-blue-600 transition-colors inline-flex items-center gap-2"
          >
            <ExternalLink className="w-4 h-4" />
            <span>Read Publication</span>
          </a>
        </div>

      </div>
    </motion.div>
  )
}
const ThesisTile = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="group relative min-h-[200px] flex w-full"
    >
      <div className="absolute inset-0 bg-gradient-to-br from-blue-500/20 to-transparent rounded-lg transform group-hover:scale-105 transition-transform" />

      <div className="relative p-4 md:p-6 rounded-lg bg-white/5 border border-white/10 backdrop-blur-sm w-full flex flex-col">

       
        <h3 className="text-xl font-bold mb-2">
          Improving Extinction Learning through Robust Off-policy Reinforcement Learning
        </h3>
         <div className="flex items-center gap-2 mb-3 text-blue-400">
          <FileText className="w-5 h-5" />
          <span className="text-sm">Master's Thesis</span>
        </div>

        <p className="text-gray-400 mb-4 line-clamp-3">
          Master's thesis exploring robust off-policy reinforcement learning
          for automated exposure therapy using simulated patient models.
        </p>

        <div className="mt-auto">
          <a
            href="/Improving_automated_extinction_learning_through_robust_off_policy_reinforcement_learning.pdf"
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 rounded-lg bg-blue-500 hover:bg-blue-600 transition-colors inline-flex items-center gap-2"
          >
            <FileText className="w-4 h-4" />
            <span>Read Thesis</span>
          </a>
        </div>

      </div>
    </motion.div>
  )
}

export const ProjectsSection = () => {
  const { repos, loading, error } = useGithubRepos('dennisglouki', 6)

  if (loading) return <div>Loading...</div>
  if (error) return <div>Error loading projects</div>

  return (
    <motion.div
      key="projects"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pb-8 px-4 md:px-6"
    >
      {/* GitHub projects */}
      {repos.map((repo, index) => (
        <motion.div
          key={repo.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
          className="group relative min-h-[200px] flex w-full"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-purple-500/20 to-transparent rounded-lg transform group-hover:scale-105 transition-transform" />

          <div className="relative p-4 md:p-6 rounded-lg bg-white/5 border border-white/10 backdrop-blur-sm w-full flex flex-col">

            <h3 className="text-xl font-bold mb-2 truncate">
              {repo.name.replace(/_/g, ' ')}
            </h3>
            <div className="flex items-center gap-2 mb-3 text-purple-400">
          <Github className="w-4 h-4" />
          <span className="text-sm">GitHub Project</span>
        </div>

            <p className="text-gray-400 mb-4 line-clamp-4 overflow-hidden">
              {repo.description || 'No description available'}
            </p>

            <div className="mt-auto">
              <a
                href={repo.html_url}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 rounded-lg bg-purple-500 hover:bg-purple-600 transition-colors inline-flex items-center gap-2"
              >
                <Github className="w-4 h-4" />
                <span>View Project</span>
              </a>
            </div>

          </div>
        </motion.div>
      ))}


      {/* Research publication */}
      <ResearchTile />
      <ThesisTile />

    </motion.div>
  )
}