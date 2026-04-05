function is_python(p)
   return p:ext() == "py" 
end

return {
   {
      should_run = is_python,
      redirect_stdout = "/tmp/ctags.log",
      commands = {
         {
            name = "Recreating tags",
            command = "ctags -R pythonx",
         },
      }
   },
}
