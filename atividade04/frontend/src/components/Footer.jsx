import React from 'react'
import {assets} from '../assets/assets'

const Footer = () => {
  return (
    <div className='flex flex-col sm:grid grid-cols-[3fr_1fr_1fr] gap-14 my-10 mt-40 text-sm'>

        <div>
            <img src={assets.logo} alt='' className='mb-5 w-32' />
            <p className='w-full md:w-2/3 text-gray-600'>123 Main Street</p>
        </div>

        <div>
            <p class ='text-xl font-medium mb-5'>
                COMPANY
            </p>
            <ul className='flex flex-col gap-1 text-gray-600'>
                <li className='text-gray-500'>Home</li>
                <li className='text-gray-500'>About us</li>
                <li className='text-gray-500'>Delivery</li>
                <li className='text-gray-500'>Privacy policy</li>
            </ul>
        </div>

        <div>
            <p class ='text-xl font-medium mb-5'>
                GET IN TOUCH
            </p>
            <ul className='flex flex-col gap-1 text-gray-600'>
                <li className='text-gray-500'>+1-212-456-7890</li>
                <li className='text-gray-500'>contact@foreveryou.com</li>
            </ul>
        </div>

        <div>
            <hr />
            <p className='py-5 text-sm text-center'>
                CopyRight &copy; 2021 ForeverYou. All rights reserved.
            </p>
        </div>

    </div>
  )
}

export default Footer