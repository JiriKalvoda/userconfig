_kam() 
{
	COMPREPLY=( $(kam -hint=$2) )
}
complete -F _kam kam
