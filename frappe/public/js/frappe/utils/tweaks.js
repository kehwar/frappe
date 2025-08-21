


// Utils

const restartable = (fn, wait = 300) => {
	if (!Number.isFinite(wait)) {
		throw new TypeError('Expected `wait` to be a finite number')
	}

	let timeout
	let currentPromise = null
	let nextArgs = null
	let resolveList = []

	const execute = async (args) => {
		// Execute the function
		const result = await fn.apply(this, args)

		// If there are new arguments (a new call was made), restart the process
		if (nextArgs) {
			const argsToUse = nextArgs
			nextArgs = null // Clear the nextArgs
			return execute(argsToUse) // Restart with the new arguments
		}

		// Resolve all promises waiting for this execution
		for (const resolve of resolveList) {
			resolve(result)
		}

		// Clear the resolve list
		resolveList = []

		// Clear the current promise when done
		currentPromise = null
		return result
	}

	return function (...args) {
		return new Promise((resolve) => {
			// Add the resolve function to the list
			resolveList.push(resolve)

			// Clear any existing timeout
			clearTimeout(timeout)

			// Set the next arguments to use if a new call is made
			nextArgs = args

			// If no current execution is happening, start the process
			if (!currentPromise) {
				timeout = setTimeout(() => {
					currentPromise = execute(nextArgs)
					nextArgs = null // Clear nextArgs after starting execution
				}, wait)
			}
		})
	}
}

// Provide

frappe.provide("frappe.tweaks");
Object.assign(frappe.tweaks, {
	restartable
})
